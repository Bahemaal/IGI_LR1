"""
Верификация требований из docs/requirements.md против работающего приложения.

Запуск:  python manage.py test apps.core.tests_requirements -v 2

Имя теста начинается с идентификатора проверяемого требования (test_FR05_...).
Тесты, помеченные @known_defect("ISS-NNN"), фиксируют РАСХОЖДЕНИЕ между требованием
и текущим поведением приложения (см. ISSUES.md). Они выполняются как «expected failure»:
сборка остаётся зелёной, а после исправления дефекта тест сообщит «unexpected success» —
тогда декоратор надо снять.
"""
import ast
import json
import statistics
import sys
import time as time_module
import unittest
from datetime import date, time, timedelta
from decimal import Decimal
from html.parser import HTMLParser
from pathlib import Path
from unittest import mock

import requests
from django.apps import apps as django_apps
from django.conf import settings
from django.contrib import admin
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import Client as HttpClient, TestCase
from django.urls import reverse
from django.utils import timezone

from .models import (
    Appointment, Article, Banner, Cabinet, Client, CompanyInfo, Contact, Doctor,
    DoctorCategory, FAQ, Order, OrderItem, Promo, Review, Sale, Schedule, Service,
    ServiceCategory, Vacancy,
)

PWD = "Str0ngP@ss!2026"
RATES = {"BYN": 1.0, "USD": 3.2, "RUB": 0.035}
BASE_DIR = Path(settings.BASE_DIR)


def known_defect(issue):
    """Расхождение с требованием, зарегистрированное в ISSUES.md."""
    def deco(func):
        func.__doc__ = f"[{issue}] " + (func.__doc__ or "")
        return unittest.expectedFailure(func)
    return deco


def future_dt(days=2, hour=10):
    base = timezone.localtime(timezone.now()).replace(hour=hour, minute=0, second=0, microsecond=0)
    return base + timedelta(days=days)


def dt_str(dt):
    return timezone.localtime(dt).strftime("%Y-%m-%dT%H:%M")


class ReqBase(TestCase):
    """Общие тестовые данные и подмена внешних сервисов (НБРБ, ipapi.co)."""

    @classmethod
    def setUpTestData(cls):
        cls.dcat = DoctorCategory.objects.create(name="Косметолог")
        cls.scat = ServiceCategory.objects.create(name="Уход")
        cls.scat2 = ServiceCategory.objects.create(name="Эпиляция")
        cls.svc_a = Service.objects.create(category=cls.scat, name="Чистка лица", price=Decimal("100.00"), duration=60)
        cls.svc_b = Service.objects.create(category=cls.scat, name="Пилинг", price=Decimal("64.00"), duration=30)
        cls.svc_c = Service.objects.create(category=cls.scat2, name="Лазерная эпиляция", price=Decimal("200.00"), duration=45)
        cls.svc_off = Service.objects.create(category=cls.scat, name="Снятая с продажи", price=Decimal("10.00"), is_active=False)
        cls.cab = Cabinet.objects.create(number="101", name="Процедурный")

        cls.doc_user = User.objects.create_user("doc", password=PWD)
        cls.doctor = Doctor.objects.create(
            user=cls.doc_user, full_name="Иванова Анна", birth_date=date(1985, 3, 15),
            category=cls.dcat, specialization="Косметолог", phone="+375 (29) 100-00-01", experience=10)
        cls.doctor.services.add(cls.svc_a, cls.svc_b)
        cls.doctor2 = Doctor.objects.create(
            full_name="Петров Пётр", birth_date=date(1980, 1, 1), category=cls.dcat,
            specialization="Дерматолог", phone="+375 (29) 100-00-02", experience=3)
        cls.doc_off = Doctor.objects.create(
            full_name="Неактивный Врач", birth_date=date(1975, 5, 5), category=cls.dcat,
            specialization="Терапевт", phone="+375 (29) 100-00-03", is_active=False)
        for wd in range(7):   # основной врач работает ежедневно 08:00-20:00
            Schedule.objects.create(doctor=cls.doctor, cabinet=cls.cab, weekday=wd,
                                    time_start=time(8, 0), time_end=time(20, 0))

        cls.user_a = User.objects.create_user("client_a", password=PWD)
        cls.cli_a = Client.objects.create(user=cls.user_a, full_name="Клиент Первый",
                                          birth_date=date(1990, 6, 1), phone="+375 (29) 200-00-01")
        cls.user_b = User.objects.create_user("client_b", password=PWD)
        cls.cli_b = Client.objects.create(user=cls.user_b, full_name="Клиент Второй",
                                          birth_date=date(1995, 7, 7), phone="+375 (29) 200-00-02")
        cls.plain_user = User.objects.create_user("plain", password=PWD)   # без профиля клиента/врача
        cls.staff = User.objects.create_superuser("root", "root@example.by", PWD)

    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)
        for target in ("apps.core.context_processors.get_exchange_rates",
                       "apps.core.templatetags.custom_tags.get_exchange_rates"):
            patcher = mock.patch(target, return_value=dict(RATES))
            patcher.start()
            self.addCleanup(patcher.stop)
        ip_patch = mock.patch("apps.core.ip_logger.get_ip_info",
                              return_value={"ip": "127.0.0.1", "error": "stub"})
        ip_patch.start()
        self.addCleanup(ip_patch.stop)

    # --- помощники ---
    def login(self, user):
        self.assertTrue(self.client.login(username=user.username, password=PWD))

    def make_appt(self, client=None, doctor=None, service=None, days=2, hour=10, status="pending"):
        return Appointment.objects.create(
            client=client or self.cli_a, doctor=doctor or self.doctor,
            service=service or self.svc_a, date_time=future_dt(days, hour), status=status)

    def appt_form(self, **kw):
        data = {"doctor": self.doctor.pk, "service": self.svc_a.pk, "cabinet": self.cab.pk,
                "date_time": dt_str(future_dt(2, 10)), "notes": ""}
        data.update(kw)
        return data

    def add_to_cart(self, service, qty=1):
        return self.client.post(f"/cart/add/{service.pk}/", {"quantity": qty})

    def checkout_data(self, **kw):
        data = {"full_name": "Тест Клиент", "phone": "+375 (29) 123-45-67", "email": "t@example.by",
                "address": "Минск", "payment_method": "card", "promo_code": ""}
        data.update(kw)
        return data


# ===================== ПУБЛИЧНАЯ ЧАСТЬ (FR-01 … FR-04, FR-18) =====================

class CatalogRequirements(ReqBase):

    def test_FR01_home_shows_latest_content_only_active(self):
        """Главная: последняя опубликованная новость, активные врачи/услуги."""
        Article.objects.create(title="Опубликованная новость", summary="s", content="c")
        Article.objects.create(title="Черновик", summary="s", content="c", is_published=False)
        Banner.objects.create(title="Баннер", image="banners/x.png")
        r = self.client.get("/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Опубликованная новость")
        self.assertNotContains(r, "Черновик")
        self.assertContains(r, "Иванова Анна")
        self.assertNotContains(r, "Неактивный Врач")
        self.assertNotContains(r, "Снятая с продажи")

    def test_FR02_services_filters_and_sort(self):
        """Каталог: категория, диапазон цен, сортировка, скрытие неактивных."""
        names = lambda r: [s.name for s in r.context["services"]]
        self.assertNotIn("Снятая с продажи", names(self.client.get("/services/")))
        self.assertEqual(names(self.client.get("/services/", {"min_price": 150})), ["Лазерная эпиляция"])
        self.assertEqual(names(self.client.get("/services/", {"max_price": 70})), ["Пилинг"])
        self.assertEqual(names(self.client.get("/services/", {"category": self.scat2.pk})), ["Лазерная эпиляция"])
        self.assertEqual(names(self.client.get("/services/", {"sort": "-price"})),
                         ["Лазерная эпиляция", "Чистка лица", "Пилинг"])

    def test_FR02_services_text_search_exact_case(self):
        """Поиск по подстроке (регистр совпадает)."""
        r = self.client.get("/services/", {"search": "эпиляц"})
        self.assertEqual([s.name for s in r.context["services"]], ["Лазерная эпиляция"])

    def test_FR02_services_search_case_insensitive_cyrillic(self):
        """Поиск не должен зависеть от регистра кириллицы («пилинг» → «Пилинг»)."""
        r = self.client.get("/services/", {"search": "пилинг"})
        self.assertEqual([s.name for s in r.context["services"]], ["Пилинг"])

    def test_FR04_doctors_search_case_insensitive_cyrillic(self):
        """Поиск врачей «иванова» должен находить «Иванова Анна»."""
        r = self.client.get("/doctors/", {"q": "иванова"})
        self.assertEqual([d.full_name for d in r.context["doctors"]], ["Иванова Анна"])

    def test_FR03_service_detail(self):
        """Карточка услуги: врачи, ≤4 похожих; неактивная → 404."""
        for i in range(6):
            Service.objects.create(category=self.scat, name=f"Доп. услуга {i}", price=10 + i)
        r = self.client.get(f"/services/{self.svc_a.pk}/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Иванова Анна")
        self.assertLessEqual(len(r.context["related"]), 4)
        self.assertEqual(self.client.get(f"/services/{self.svc_off.pk}/").status_code, 404)

    def test_FR04_doctors_list_detail_schedule(self):
        """Врачи: только активные, сортировка по стажу, детальная страница с расписанием."""
        r = self.client.get("/doctors/", {"sort": "-experience"})
        self.assertEqual([d.full_name for d in r.context["doctors"]], ["Иванова Анна", "Петров Пётр"])
        d = self.client.get(f"/doctors/{self.doctor.pk}/")
        self.assertEqual(d.status_code, 200)
        self.assertEqual(len(d.context["schedules"]), 7)
        self.assertEqual(self.client.get(f"/doctors/{self.doc_off.pk}/").status_code, 404)

    def test_FR18_info_pages(self):
        """Информационные разделы: только опубликованное/открытое/актуальное."""
        Article.objects.create(title="Видна", summary="s", content="c")
        hidden = Article.objects.create(title="Скрыта", summary="s", content="c", is_published=False)
        Vacancy.objects.create(title="Открытая вакансия", description="d")
        Vacancy.objects.create(title="Закрытая вакансия", description="d", is_open=False)
        today = date.today()
        Promo.objects.create(code="NOW", discount_percent=5, valid_from=today - timedelta(1), valid_to=today + timedelta(5))
        Promo.objects.create(code="OLD", discount_percent=5, valid_from=today - timedelta(30), valid_to=today - timedelta(10))
        FAQ.objects.create(question="Вопрос?", answer="Ответ")
        Contact.objects.create(full_name="Админ", position="Администратор", phone="+375 (29) 000-00-00")
        self.assertContains(self.client.get("/news/"), "Видна")
        self.assertNotContains(self.client.get("/news/"), "Скрыта")
        self.assertEqual(self.client.get(f"/news/{hidden.pk}/").status_code, 404)
        self.assertContains(self.client.get("/vacancies/"), "Открытая вакансия")
        self.assertNotContains(self.client.get("/vacancies/"), "Закрытая вакансия")
        promos = self.client.get("/promos/")
        self.assertEqual([p.code for p in promos.context["current"]], ["NOW"])
        self.assertEqual([p.code for p in promos.context["archived"]], ["OLD"])
        for url in ("/faq/", "/contacts/", "/privacy/", "/about/", "/reviews/"):
            self.assertEqual(self.client.get(url).status_code, 200, url)

    def test_FR18_about_video_embed(self):
        """«О компании»: ссылка YouTube преобразуется во встраиваемую (nocookie)."""
        CompanyInfo.objects.create(name="Центр", description="d", video_url="https://youtu.be/abc123?t=5")
        r = self.client.get("/about/")
        self.assertEqual(r.context["video_embed_url"], "https://www.youtube-nocookie.com/embed/abc123")


# ===================== КОРЗИНА И ЗАКАЗЫ (FR-05 … FR-08) =====================

class CartOrderRequirements(ReqBase):

    def test_FR05_cart_add_update_remove(self):
        """Корзина в сессии: добавить, суммировать, обновить (0 = удалить), удалить."""
        self.add_to_cart(self.svc_a, 2)
        self.add_to_cart(self.svc_a, 1)
        self.assertEqual(self.client.session["cart"], {str(self.svc_a.pk): 3})
        r = self.client.get("/cart/")
        self.assertEqual(r.context["cart_total"], Decimal("300.00"))
        self.client.post(f"/cart/update/{self.svc_a.pk}/", {"quantity": 5})
        self.assertEqual(self.client.session["cart"], {str(self.svc_a.pk): 5})
        self.client.post(f"/cart/update/{self.svc_a.pk}/", {"quantity": 0})
        self.assertEqual(self.client.session["cart"], {})
        self.add_to_cart(self.svc_b)
        self.client.post(f"/cart/remove/{self.svc_b.pk}/")
        self.assertEqual(self.client.session["cart"], {})

    def test_FR05_cart_rejects_inactive_and_bad_quantity(self):
        """Неактивную услугу добавить нельзя; некорректное количество → 1."""
        self.assertEqual(self.add_to_cart(self.svc_off).status_code, 404)
        self.client.post(f"/cart/add/{self.svc_b.pk}/", {"quantity": "abc"})
        self.client.post(f"/cart/add/{self.svc_c.pk}/", {"quantity": -7})
        self.assertEqual(self.client.session["cart"], {str(self.svc_b.pk): 1, str(self.svc_c.pk): 1})

    def test_FR06_checkout_empty_cart_redirects(self):
        r = self.client.get("/checkout/")
        self.assertRedirects(r, "/services/", fetch_redirect_response=False)

    def test_FR06_checkout_creates_order_and_clears_cart(self):
        """Оформление: заказ + позиции со снимком цены, корзина очищена, страница успеха."""
        self.add_to_cart(self.svc_a, 2)
        self.add_to_cart(self.svc_b, 1)
        r = self.client.post("/checkout/", self.checkout_data())
        order = Order.objects.get()
        self.assertRedirects(r, f"/order/{order.pk}/success/", fetch_redirect_response=False)
        self.assertEqual(order.items.count(), 2)
        self.assertEqual(order.total_amount, Decimal("264.00"))
        self.assertEqual(self.client.session["cart"], {})

    def test_FR06_checkout_rejects_bad_phone(self):
        self.add_to_cart(self.svc_a)
        r = self.client.post("/checkout/", self.checkout_data(phone="80291234567"))
        self.assertEqual(r.status_code, 200)
        self.assertIn("phone", r.context["form"].errors)
        self.assertEqual(Order.objects.count(), 0)

    def test_FR06_checkout_prefills_authenticated_client(self):
        self.login(self.user_a)
        self.add_to_cart(self.svc_a)
        r = self.client.get("/checkout/")
        self.assertEqual(r.context["form"].initial["full_name"], "Клиент Первый")

    def test_FR07_promo_unknown_or_expired_rejected(self):
        today = date.today()
        Promo.objects.create(code="OLD", discount_percent=10, valid_from=today - timedelta(30), valid_to=today - timedelta(1))
        self.add_to_cart(self.svc_a)
        for code in ("NOPE", "old"):
            r = self.client.post("/checkout/", self.checkout_data(promo_code=code))
            self.assertIn("promo_code", r.context["form"].errors, code)
        self.assertEqual(Order.objects.count(), 0)

    def test_FR07_valid_promo_applies_discount(self):
        """Действующий промокод 10% уменьшает итог: 2×100.00 → 180.00."""
        today = date.today()
        Promo.objects.create(code="SALE10", discount_percent=10, valid_from=today - timedelta(1), valid_to=today + timedelta(30))
        self.add_to_cart(self.svc_a, 2)
        self.client.post("/checkout/", self.checkout_data(promo_code="sale10"))
        self.assertEqual(Order.objects.get().total_amount, Decimal("180.00"))

    def test_FR08_cash_order_is_new_until_paid(self):
        """Оплата «наличными при визите»: заказ создаётся «Новый», а не «Оплачен»."""
        self.add_to_cart(self.svc_a)
        self.client.post("/checkout/", self.checkout_data(payment_method="cash"))
        self.assertEqual(Order.objects.get().status, "new")

    def test_FR06_order_success_not_visible_to_strangers(self):
        """Страница заказа с ПДн не должна открываться посторонним по номеру."""
        order = Order.objects.create(full_name="Секретный Клиент", phone="+375 (29) 999-99-99",
                                     total_amount=Decimal("10.00"), status="new")
        stranger = HttpClient()
        r = stranger.get(f"/order/{order.pk}/success/")
        self.assertNotEqual(r.status_code, 200)

    def test_NFR09_order_item_price_is_snapshot(self):
        """Цена позиции заказа фиксируется на момент оформления."""
        self.add_to_cart(self.svc_a)
        self.client.post("/checkout/", self.checkout_data())
        Service.objects.filter(pk=self.svc_a.pk).update(price=Decimal("999.00"))
        self.assertEqual(OrderItem.objects.get().price, Decimal("100.00"))


# ===================== УЧЁТНЫЕ ЗАПИСИ (FR-09 … FR-11) =====================

class AccountRequirements(ReqBase):

    def reg_data(self, **kw):
        data = {"username": "newbie", "password1": PWD, "password2": PWD, "full_name": "Новый Клиент",
                "birth_date": "1995-01-01", "phone": "+375 (29) 555-55-55", "email": "n@example.by", "address": ""}
        data.update(kw)
        return data

    def test_FR09_registration_creates_user_client_and_logs_in(self):
        r = self.client.post("/register/client/", self.reg_data())
        self.assertRedirects(r, "/", fetch_redirect_response=False)
        user = User.objects.get(username="newbie")
        self.assertEqual(user.client_profile.full_name, "Новый Клиент")
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)

    def test_FR09_registration_validation(self):
        bad = {
            "под 18 лет": self.reg_data(birth_date=(date.today() - timedelta(days=365 * 15)).isoformat()),
            "телефон": self.reg_data(phone="80291234567"),
            "пароли": self.reg_data(password2="другой"),
            "дубликат логина": self.reg_data(username="client_a"),
        }
        for name, data in bad.items():
            r = self.client.post("/register/client/", data)
            self.assertEqual(r.status_code, 200, name)
        self.assertFalse(User.objects.filter(username="newbie").exists())

    def test_FR10_login_logout(self):
        r = self.client.post("/login/", {"username": "client_a", "password": "wrong"})
        self.assertEqual(r.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)
        r = self.client.post("/login/", {"username": "client_a", "password": PWD})
        self.assertRedirects(r, "/", fetch_redirect_response=False)
        r = self.client.post("/logout/")
        self.assertEqual(r.status_code, 302)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_FR10_login_returns_to_requested_page(self):
        """После входа — переход на страницу из ?next= (например /profile/)."""
        r = self.client.get("/profile/")
        self.assertEqual(r["Location"], "/login/?next=/profile/")
        r = self.client.post("/login/?next=/profile/", {"username": "client_a", "password": PWD, "next": "/profile/"})
        self.assertEqual(r["Location"], "/profile/")

    def test_FR11_profile_shows_only_own_appointments(self):
        self.make_appt(self.cli_a, days=2)
        self.make_appt(self.cli_a, days=3, status="completed")
        self.make_appt(self.cli_b, days=4)
        self.login(self.user_a)
        r = self.client.get("/profile/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.context["appointments"]), 2)
        self.assertEqual(r.context["total_appointments"], 2)
        self.assertEqual(r.context["completed"], 1)

    def test_FR11_profile_requires_client(self):
        self.assertRedirects(self.client.get("/profile/"), "/login/?next=/profile/", fetch_redirect_response=False)
        self.login(self.doc_user)
        self.assertRedirects(self.client.get("/profile/"), "/", fetch_redirect_response=False)


# ===================== ЗАПИСИ НА ПРИЁМ (FR-12 … FR-16) =====================

class AppointmentRequirements(ReqBase):

    def test_FR12_create_appointment_ok(self):
        self.login(self.user_a)
        r = self.client.post("/appointment/create/", self.appt_form())
        self.assertRedirects(r, "/profile/", fetch_redirect_response=False)
        appt = Appointment.objects.get()
        self.assertEqual((appt.client, appt.status), (self.cli_a, "pending"))

    def test_FR12_create_appointment_in_past_rejected(self):
        self.login(self.user_a)
        r = self.client.post("/appointment/create/", self.appt_form(date_time=dt_str(timezone.now() - timedelta(days=1))))
        self.assertEqual(r.status_code, 200)
        self.assertIn("date_time", r.context["form"].errors)
        self.assertEqual(Appointment.objects.count(), 0)

    def test_FR12_create_requires_login_and_client_profile(self):
        self.assertEqual(self.client.get("/appointment/create/").status_code, 302)
        self.login(self.plain_user)
        self.assertRedirects(self.client.get("/appointment/create/"), "/register/client/", fetch_redirect_response=False)

    def test_FR12_double_booking_rejected(self):
        """Тот же врач в то же время нельзя записать двум клиентам."""
        self.login(self.user_a)
        self.client.post("/appointment/create/", self.appt_form())
        self.client.logout()
        self.login(self.user_b)
        self.client.post("/appointment/create/", self.appt_form())
        self.assertEqual(Appointment.objects.count(), 1)

    def test_FR12_doctor_must_provide_service(self):
        """Врач, не оказывающий услугу, недоступен для записи на неё."""
        self.login(self.user_a)
        self.client.post("/appointment/create/", self.appt_form(service=self.svc_c.pk))   # врач оказывает только A и B
        self.assertEqual(Appointment.objects.count(), 0)

    def test_FR12_inactive_doctor_not_bookable(self):
        self.login(self.user_a)
        self.client.post("/appointment/create/", self.appt_form(doctor=self.doc_off.pk))
        self.assertEqual(Appointment.objects.count(), 0)

    def test_FR12_booking_only_within_doctor_schedule(self):
        """Запись на 23:00 при графике 08:00–20:00 должна отклоняться."""
        self.login(self.user_a)
        self.client.post("/appointment/create/", self.appt_form(date_time=dt_str(future_dt(2, 23))))
        self.assertEqual(Appointment.objects.count(), 0)

    def test_FR13_owner_can_edit_notes(self):
        appt = self.make_appt()
        self.login(self.user_a)
        r = self.client.post(f"/appointment/{appt.pk}/edit/", {"status": "pending", "notes": "Аллергия на латекс"})
        self.assertEqual(r.status_code, 302)
        appt.refresh_from_db()
        self.assertEqual(appt.notes, "Аллергия на латекс")

    def test_FR13_client_cannot_self_confirm_or_complete(self):
        """Клиент не должен переводить свою запись в «Подтверждено/Завершено»."""
        appt = self.make_appt()
        self.login(self.user_a)
        self.client.post(f"/appointment/{appt.pk}/edit/", {"status": "completed", "notes": ""})
        appt.refresh_from_db()
        self.assertEqual(appt.status, "pending")

    def test_FR15_client_cannot_touch_foreign_appointment(self):
        appt = self.make_appt(self.cli_b)
        self.login(self.user_a)
        self.client.post(f"/appointment/{appt.pk}/edit/", {"status": "cancelled", "notes": "hack"})
        self.client.post(f"/appointment/{appt.pk}/delete/")
        appt.refresh_from_db()
        self.assertEqual((appt.status, appt.notes), ("pending", ""))

    def test_FR15_user_without_role_cannot_edit_appointment(self):
        """Пользователь без профиля клиента/врача не должен менять чужие записи."""
        appt = self.make_appt()
        self.login(self.plain_user)
        self.client.post(f"/appointment/{appt.pk}/edit/", {"status": "cancelled", "notes": ""})
        appt.refresh_from_db()
        self.assertEqual(appt.status, "pending")

    def test_FR15_user_without_role_cannot_delete_appointment(self):
        appt = self.make_appt()
        self.login(self.plain_user)
        self.client.post(f"/appointment/{appt.pk}/delete/")
        self.assertTrue(Appointment.objects.filter(pk=appt.pk).exists())

    def test_FR15_doctor_cannot_delete_foreign_appointment(self):
        appt = self.make_appt(doctor=self.doctor2)    # запись к другому врачу
        self.login(self.doc_user)
        self.client.post(f"/appointment/{appt.pk}/delete/")
        self.assertTrue(Appointment.objects.filter(pk=appt.pk).exists())

    def test_FR14_cancel_keeps_record_with_cancelled_status(self):
        """Отмена записи: запись сохраняется со статусом «Отменено»."""
        appt = self.make_appt()
        self.login(self.user_a)
        self.client.post(f"/appointment/{appt.pk}/delete/")
        appt.refresh_from_db()
        self.assertEqual(appt.status, "cancelled")

    def test_FR14_completed_appointment_with_payment_cannot_be_cancelled(self):
        """Завершённый приём с оплатой не удаляется (иначе каскадно теряется Sale)."""
        appt = self.make_appt(status="completed")
        Sale.objects.create(appointment=appt, amount=Decimal("100.00"))
        self.login(self.user_a)
        self.client.post(f"/appointment/{appt.pk}/delete/")
        self.assertTrue(Sale.objects.filter(appointment=appt).exists())

    def test_FR16_doctor_cabinet_shows_own_schedule_and_appointments(self):
        mine = self.make_appt()
        self.make_appt(doctor=self.doctor2, days=3)
        self.login(self.doc_user)
        r = self.client.get("/doctor/profile/")
        self.assertEqual([a.pk for a in r.context["appointments"]], [mine.pk])
        self.assertEqual(len(r.context["schedules"]), 7)
        self.client.logout()
        self.login(self.user_a)
        self.assertRedirects(self.client.get("/doctor/profile/"), "/", fetch_redirect_response=False)

    def test_FR16_doctor_returns_to_cabinet_after_status_change(self):
        """Врач подтверждает приём и возвращается в «Кабинет врача», а не в «Мой профиль»."""
        appt = self.make_appt()
        self.login(self.doc_user)
        r = self.client.post(f"/appointment/{appt.pk}/edit/", {"status": "confirmed", "notes": ""})
        self.assertEqual(r["Location"], "/doctor/profile/")


# ===================== ОТЗЫВЫ (FR-17) =====================

class ReviewRequirements(ReqBase):

    def test_FR17_only_approved_reviews_listed(self):
        Review.objects.create(client=self.cli_a, rating=5, text="Одобренный", is_approved=True)
        Review.objects.create(client=self.cli_b, rating=1, text="Скрытый", is_approved=False)
        r = self.client.get("/reviews/")
        self.assertEqual([x.text for x in r.context["reviews"]], ["Одобренный"])

    def test_FR17_add_review_rules(self):
        self.assertEqual(self.client.post("/reviews/add/", {"rating": 5, "text": "x"}).status_code, 302)
        self.assertEqual(Review.objects.count(), 0)                       # аноним
        self.login(self.plain_user)
        self.client.post("/reviews/add/", {"rating": 5, "text": "Не клиент"})
        self.assertEqual(Review.objects.count(), 0)                       # не клиент
        self.client.logout()
        self.login(self.user_a)
        self.client.post("/reviews/add/", {"rating": 6, "text": "Оценка вне диапазона"})
        self.assertEqual(Review.objects.count(), 0)                       # рейтинг 1..5
        self.client.post("/reviews/add/", {"rating": 5, "text": "Отлично"})
        self.assertEqual(Review.objects.get().client, self.cli_a)

    def test_FR17_new_review_awaits_moderation(self):
        """Новый отзыв публикуется только после одобрения администратором."""
        self.login(self.user_a)
        self.client.post("/reviews/add/", {"rating": 5, "text": "Отлично"})
        self.assertFalse(Review.objects.get().is_approved)


# ===================== ВАЛЮТА, СТАТИСТИКА, АДМИНКА (FR-19 … FR-25) =====================

class MiscRequirements(ReqBase):

    def set_currency(self, code):
        return self.client.post("/set-currency/", data=json.dumps({"currency": code}), content_type="application/json")

    def test_FR19_currency_switch_converts_prices(self):
        r = self.set_currency("USD")
        self.assertEqual((r.status_code, r.json()["currency"]), (200, "USD"))
        self.assertEqual(self.client.session["currency"], "USD")
        r = self.client.get("/services/")
        self.assertRegex(r.content.decode(), r"20[.,]00 USD")           # 64 BYN / 3.2
        self.set_currency("RUB")
        self.assertRegex(self.client.get("/services/").content.decode(), r"1\s?828[.,]57 RUB")   # 64 / 0.035

    def test_FR19_currency_invalid_rejected(self):
        self.assertEqual(self.set_currency("EUR").status_code, 400)
        self.assertEqual(self.client.get("/set-currency/").status_code, 400)

    def test_FR20_statistics_for_staff_only(self):
        self.assertEqual(self.client.get("/statistics/").status_code, 302)
        self.login(self.user_a)
        self.assertEqual(self.client.get("/statistics/").status_code, 302)
        self.client.logout()
        self.login(self.staff)
        done = self.make_appt(status="completed")
        self.make_appt(days=5)
        Sale.objects.create(appointment=done, amount=Decimal("100.00"))
        r = self.client.get("/statistics/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual((r.context["total_appointments"], r.context["completed"], r.context["upcoming"]), (2, 1, 2))
        self.assertEqual(r.context["revenue"], Decimal("100.00"))
        self.assertEqual(r.context["price_mean"], 93.5)
        self.assertEqual(r.context["price_median"], 82.0)

    def test_FR20_revenue_includes_paid_online_orders(self):
        """Выручка = оплаты по приёмам + оплаченные онлайн-заказы."""
        done = self.make_appt(status="completed")
        Sale.objects.create(appointment=done, amount=Decimal("100.00"))
        Order.objects.create(full_name="Онлайн", phone="+375 (29) 111-11-11", total_amount=Decimal("50.00"), status="paid")
        self.login(self.staff)
        self.assertEqual(self.client.get("/statistics/").context["revenue"], Decimal("150.00"))

    def test_FR21_admin_registers_every_model_and_changelists_open(self):
        """Все сущности доступны в админке (OrderItem — только как inline заказа)."""
        self.login(self.staff)
        for model in django_apps.get_app_config("core").get_models():
            if model is OrderItem:
                continue
            self.assertTrue(admin.site.is_registered(model), model.__name__)
            url = reverse(f"admin:core_{model._meta.model_name}_changelist")
            self.assertEqual(self.client.get(url).status_code, 200, url)
        self.client.logout()
        self.assertEqual(self.client.get("/admin/").status_code, 302)

    def test_FR22_profile_page_survives_ip_service_error(self):
        self.login(self.user_a)
        r = self.client.get("/profile/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "127.0.0.1")

    def test_FR23_model_validators(self):
        d = Doctor(full_name="Х", birth_date=date(1990, 1, 1), category=self.dcat, specialization="s", phone="123")
        with self.assertRaises(ValidationError):
            d.full_clean()
        c = Client(full_name="Х", birth_date=date.today() - timedelta(days=365 * 10), phone="+375 (29) 123-45-67")
        with self.assertRaises(ValidationError):
            c.full_clean()

    def test_FR24_schedule_end_must_be_after_start(self):
        s = Schedule(doctor=self.doctor, cabinet=self.cab, weekday=0, time_start=time(18, 0), time_end=time(9, 0))
        with self.assertRaises(ValidationError):
            s.full_clean()

    def test_FR24_sale_one_per_appointment(self):
        appt = self.make_appt(status="completed")
        Sale.objects.create(appointment=appt, amount=Decimal("100.00"))
        from django.db import IntegrityError, transaction
        with self.assertRaises(IntegrityError), transaction.atomic():
            Sale.objects.create(appointment=appt, amount=Decimal("1.00"))

    def test_FR25_multitasking_demo_page(self):
        self.login(self.staff)
        started = time_module.perf_counter()
        r = self.client.get("/multitasking/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.context["thread_results"]), 5)
        self.assertEqual(len(r.context["async_results"]), 10)
        self.assertEqual(len(r.context["mp_top10"]), 10)
        print(f"\n[MEASURE] /multitasking/ выполнялась {time_module.perf_counter() - started:.2f} с", file=sys.stderr)


# ===================== НЕФУНКЦИОНАЛЬНЫЕ (NFR-01 … NFR-09) =====================

class NonFunctionalRequirements(ReqBase):

    def test_NFR01_public_pages_p95_under_1s(self):
        """p95 времени ответа публичных страниц ≤ 1 с (тестовый клиент, без сети)."""
        Article.objects.create(title="Н", summary="s", content="c")
        samples = []
        for url in ("/", "/services/", "/doctors/", "/news/", "/faq/"):
            for _ in range(20):
                t0 = time_module.perf_counter()
                self.assertEqual(self.client.get(url).status_code, 200)
                samples.append(time_module.perf_counter() - t0)
        p95 = statistics.quantiles(samples, n=20)[-1]
        print(f"\n[MEASURE] NFR-01: n={len(samples)}, median={statistics.median(samples)*1000:.0f} мс, "
              f"p95={p95*1000:.0f} мс, max={max(samples)*1000:.0f} мс", file=sys.stderr)
        self.assertLess(p95, 1.0)

    def test_NFR02_protected_pages_require_login(self):
        for url in ("/profile/", "/appointment/create/", "/appointment/1/edit/", "/appointment/1/delete/",
                    "/doctor/profile/", "/statistics/", "/reviews/add/"):
            r = self.client.get(url)
            self.assertEqual(r.status_code, 302, url)
            self.assertIn("login", r["Location"], url)

    def test_NFR02_passwords_are_hashed(self):
        self.assertTrue(self.user_a.password.startswith("pbkdf2_sha256$"))

    def test_NFR02_csrf_enforced_on_forms(self):
        strict = HttpClient(enforce_csrf_checks=True)
        self.assertEqual(strict.post("/login/", {"username": "x", "password": "y"}).status_code, 403)
        self.assertEqual(strict.post(f"/cart/add/{self.svc_a.pk}/", {"quantity": 1}).status_code, 403)

    def test_NFR02_csrf_enforced_on_set_currency(self):
        strict = HttpClient(enforce_csrf_checks=True)
        r = strict.post("/set-currency/", data=json.dumps({"currency": "USD"}), content_type="application/json")
        self.assertEqual(r.status_code, 403)

    def test_NFR02_cart_add_does_not_change_state_on_get(self):
        self.client.get(f"/cart/add/{self.svc_a.pk}/")
        self.assertEqual(self.client.session.get("cart", {}), {})

    def test_NFR02_no_open_redirect_in_cart_add(self):
        r = self.client.post(f"/cart/add/{self.svc_a.pk}/", {"quantity": 1, "next": "https://evil.example/phish"})
        self.assertFalse(r["Location"].startswith("http"))

    def test_NFR02_heavy_demo_page_not_public(self):
        """Ресурсоёмкая страница (4 процесса на запрос) не должна быть открыта анониму."""
        self.assertNotEqual(self.client.get("/multitasking/").status_code, 200)

    @known_defect("ISS-019")
    def test_NFR03_production_ready_settings(self):
        """DEBUG выключен, SECRET_KEY не «django-insecure», ALLOWED_HOSTS не ['*']."""
        import cosmet_center.settings as s
        self.assertFalse(s.DEBUG)
        self.assertNotIn("django-insecure", s.SECRET_KEY)
        self.assertNotEqual(s.ALLOWED_HOSTS, ["*"])

    def test_NFR04_basic_accessibility_markup(self):
        problems = []
        pages = [("/", None), ("/services/", None), ("/doctors/", None), ("/login/", None),
                 ("/register/client/", None), ("/appointment/create/", self.user_a)]
        for url, user in pages:
            self.client.logout()
            if user:
                self.login(user)
            checker = A11yChecker()
            checker.feed(self.client.get(url).content.decode())
            problems += [f"{url}: {p}" for p in checker.problems()]
        self.assertEqual(problems, [])

    def test_NFR04_every_form_control_has_label(self):
        """Каждое поле формы связано с подписью (в т.ч. переключатель валюты)."""
        checker = A11yChecker()
        checker.feed(self.client.get("/services/").content.decode())
        self.assertEqual(checker.unlabelled, [])

    def test_NFR05_declared_dependencies_match_imports(self):
        """Все сторонние пакеты, импортируемые рабочим кодом, перечислены в requirements.txt."""
        dist = {"django": "django", "requests": "requests", "PIL": "pillow", "psycopg2": "psycopg2-binary"}
        listed = (BASE_DIR / "requirements.txt").read_text(encoding="utf-8").lower()
        used = set()
        sources = list(BASE_DIR.joinpath("apps").rglob("*.py")) + list(BASE_DIR.joinpath("cosmet_center").rglob("*.py"))
        for path in sources:
            if path.name.startswith("test") or "migrations" in path.parts:
                continue
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                if isinstance(node, ast.Import):
                    used |= {a.name.split(".")[0] for a in node.names}
                elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                    used.add(node.module.split(".")[0])
        third_party = used - set(sys.stdlib_module_names) - {"apps", "cosmet_center"}
        missing = sorted(m for m in third_party if dist.get(m, m).lower() not in listed)
        self.assertEqual(missing, [], f"не указаны в requirements.txt: {missing}")

    def test_NFR05_test_dependencies_declared(self):
        """Пакет python-dateutil, нужный существующим тестам, указан в зависимостях."""
        listed = (BASE_DIR / "requirements.txt").read_text(encoding="utf-8").lower()
        self.assertNotIn("from dateutil", (BASE_DIR / "apps/core/tests.py").read_text(encoding="utf-8"))

    @known_defect("ISS-002")
    def test_NFR05_compose_database_matches_settings(self):
        """docker-compose поднимает PostgreSQL → настройки должны использовать PostgreSQL."""
        import cosmet_center.settings as s
        compose = (BASE_DIR / "docker-compose.yml").read_text(encoding="utf-8")
        self.assertIn("postgres", compose)
        self.assertIn("postgresql", s.DATABASES["default"]["ENGINE"])

    def test_NFR05_initial_fixture_loads(self):
        call_command("loaddata", str(BASE_DIR / "apps" / "core" / "fixtures" / "initial_data.json"), verbosity=0)
        self.assertGreaterEqual(Service.objects.filter(is_active=True).count(), 12)

    def test_NFR07_localization_settings(self):
        import cosmet_center.settings as s
        self.assertEqual((s.LANGUAGE_CODE, s.TIME_ZONE, s.DEFAULT_CURRENCY), ("ru-ru", "Europe/Minsk", "BYN"))
        self.assertIn('<html lang="ru">', self.client.get("/services/").content.decode())

    def test_NFR08_key_events_are_logged(self):
        with self.assertLogs("apps.core", level="INFO") as cm:
            self.client.post("/register/client/", {
                "username": "logged", "password1": PWD, "password2": PWD, "full_name": "Лог Тест",
                "birth_date": "1990-01-01", "phone": "+375 (29) 777-77-77", "email": "l@example.by"})
            self.client.post("/appointment/create/", self.appt_form())
            self.add_to_cart(self.svc_a)
            self.client.post("/checkout/", self.checkout_data())
        text = "\n".join(cm.output)
        for marker in ("registered", "Appointment created", "New order"):
            self.assertIn(marker, text)

    def test_NFR08_appointment_update_and_delete_log_records_are_valid(self):
        """Записи журнала об изменении/отмене приёма форматируются без ошибок."""
        appt = self.make_appt()
        self.login(self.user_a)
        with mock.patch("apps.core.views.logger") as lg:
            self.client.post(f"/appointment/{appt.pk}/edit/", {"status": "pending", "notes": "x"})
            self.client.post(f"/appointment/{appt.pk}/delete/")
        self.assertEqual(lg.info.call_count, 2)
        for call in lg.info.call_args_list:
            message, *args = call.args
            message % tuple(args)      # TypeError: %d format: a real number is required, not str


class ExternalServiceFailureRequirements(TestCase):
    """NFR-06: отказ внешних сервисов (НБРБ, ipapi.co) не должен ломать сайт."""

    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)

    def test_NFR06_nbrb_failure_uses_fallback_rates_and_pages_render(self):
        from . import currency
        with mock.patch("apps.core.currency.requests.get", side_effect=requests.ConnectionError("down")):
            rates = currency.get_exchange_rates()
            self.assertEqual(set(rates), {"BYN", "USD", "RUB"})
            cache.clear()
            self.assertEqual(self.client.get("/services/").status_code, 200)

    def test_NFR06_ip_lookup_failure_is_cached(self):
        """Ошибка ipapi.co кэшируется, иначе каждая загрузка профиля ждёт таймаут 6 с."""
        from . import ip_logger
        with mock.patch("apps.core.ip_logger.requests.get", side_effect=requests.Timeout("slow")) as m:
            ip_logger.get_ip_info("8.8.8.8")
            ip_logger.get_ip_info("8.8.8.8")
            self.assertEqual(m.call_count, 1)


class A11yChecker(HTMLParser):
    """Простейшая проверка разметки: lang, viewport, alt у изображений, подписи полей."""
    SKIP_TYPES = {"hidden", "submit", "button", "image", "reset"}

    def __init__(self):
        super().__init__()
        self.lang = self.viewport = False
        self.label_for, self.controls, self.images_without_alt = set(), [], 0
        self._label_depth = 0
        self.unlabelled = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "html" and a.get("lang"):
            self.lang = True
        if tag == "meta" and a.get("name") == "viewport":
            self.viewport = True
        if tag == "img" and "alt" not in a:
            self.images_without_alt += 1
        if tag == "label":
            self._label_depth += 1
            if a.get("for"):
                self.label_for.add(a["for"])
        if tag in ("input", "select", "textarea") and a.get("type", "text") not in self.SKIP_TYPES:
            self.controls.append((a, self._label_depth > 0))

    def handle_endtag(self, tag):
        if tag == "label" and self._label_depth:
            self._label_depth -= 1

    def problems(self):
        out = []
        if not self.lang:
            out.append("нет lang у <html>")
        if not self.viewport:
            out.append("нет meta viewport")
        if self.images_without_alt:
            out.append(f"изображений без alt: {self.images_without_alt}")
        return out

    def feed(self, data):
        super().feed(data)
        self.unlabelled = [
            a.get("name") or a.get("id") or "?" for a, inside in self.controls
            if not (inside or a.get("id") in self.label_for or a.get("aria-label")
                    or a.get("aria-labelledby") or a.get("title"))
        ]
