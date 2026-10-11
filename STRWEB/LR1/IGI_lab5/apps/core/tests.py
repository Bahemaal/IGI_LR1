from django.test import TestCase, Client as TestClient
from django.contrib.auth.models import User
from django.urls import reverse, resolve
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import date, timedelta, time
import re

from .models import (
    DoctorCategory, Doctor, Client, ServiceCategory, Service,
    Cabinet, Appointment, Sale, Schedule, Promo,
    Article, FAQ, Contact, Vacancy, Review, CompanyInfo, validate_phone_by, validate_adult
)
from .forms import ClientRegistrationForm, AppointmentForm, ReviewForm, ServiceFilterForm


# ─────────────── MODEL TESTS ───────────────

class ValidatorTests(TestCase):

    def test_phone_valid(self):
        """Корректный номер не вызывает исключения"""
        validate_phone_by("+375 (29) 123-45-67")

    def test_phone_invalid(self):
        """Неверный формат вызывает ValidationError"""
        with self.assertRaises(ValidationError):
            validate_phone_by("80291234567")

    def test_phone_invalid_short(self):
        with self.assertRaises(ValidationError):
            validate_phone_by("+375291234567")

    def test_adult_valid(self):
        bd = date.today() - timedelta(days=365 * 20)
        validate_adult(bd)  # не должно бросать

    def test_adult_under_18(self):
        bd = date.today() - timedelta(days=365 * 17)
        with self.assertRaises(ValidationError):
            validate_adult(bd)

    def test_adult_exactly_18(self):
        from dateutil.relativedelta import relativedelta
        try:
            bd = date.today() - relativedelta(years=18)
            validate_adult(bd)  # ровно 18 — должно пройти
        except ImportError:
            bd = date.today().replace(year=date.today().year - 18)
            validate_adult(bd)


class DoctorCategoryModelTest(TestCase):

    def setUp(self):
        self.cat = DoctorCategory.objects.create(name="Дерматология", description="Кожа")

    def test_str(self):
        self.assertEqual(str(self.cat), "Дерматология")

    def test_verbose_name(self):
        self.assertEqual(DoctorCategory._meta.verbose_name, "Категория врача")


class ServiceModelTest(TestCase):

    def setUp(self):
        sc = ServiceCategory.objects.create(name="Косметология")
        self.service = Service.objects.create(
            category=sc, name="Чистка лица", price=50.00, duration=60
        )

    def test_str_contains_name(self):
        self.assertIn("Чистка лица", str(self.service))

    def test_price_stored(self):
        self.assertEqual(float(self.service.price), 50.0)

    def test_is_active_default(self):
        self.assertTrue(self.service.is_active)


class DoctorModelTest(TestCase):

    def setUp(self):
        cat = DoctorCategory.objects.create(name="Дерматология")
        self.doctor = Doctor.objects.create(
            full_name="Иванова Мария",
            birth_date=date(1985, 3, 15),
            category=cat,
            specialization="Косметолог",
            phone="+375 (29) 100-00-01",
            experience=10,
        )

    def test_str(self):
        self.assertEqual(str(self.doctor), "Иванова Мария")

    def test_age_property(self):
        age = self.doctor.age
        self.assertGreater(age, 18)

    def test_m2m_services(self):
        sc = ServiceCategory.objects.create(name="Уход")
        s = Service.objects.create(category=sc, name="Пилинг", price=30, duration=45)
        self.doctor.services.add(s)
        self.assertIn(s, self.doctor.services.all())


class ClientModelTest(TestCase):

    def setUp(self):
        user = User.objects.create_user("testuser", password="pass1234")
        self.client_obj = Client.objects.create(
            user=user,
            full_name="Петров Иван",
            birth_date=date(1990, 6, 1),
            phone="+375 (33) 200-00-02",
        )

    def test_str(self):
        self.assertEqual(str(self.client_obj), "Петров Иван")

    def test_age(self):
        self.assertGreater(self.client_obj.age, 18)

    def test_one_to_one_user(self):
        self.assertEqual(self.client_obj.user.username, "testuser")


class PromoModelTest(TestCase):

    def test_is_current_true(self):
        p = Promo.objects.create(
            code="SUMMER25",
            discount_percent=25,
            valid_from=date.today() - timedelta(days=1),
            valid_to=date.today() + timedelta(days=10),
        )
        self.assertTrue(p.is_current)

    def test_is_current_false_expired(self):
        p = Promo.objects.create(
            code="OLD10",
            discount_percent=10,
            valid_from=date(2020, 1, 1),
            valid_to=date(2020, 12, 31),
        )
        self.assertFalse(p.is_current)


class AppointmentModelTest(TestCase):

    def setUp(self):
        cat = DoctorCategory.objects.create(name="Дерматология")
        doctor = Doctor.objects.create(
            full_name="Сидорова Анна",
            birth_date=date(1982, 1, 1),
            category=cat,
            specialization="Косметолог",
            phone="+375 (29) 111-11-11",
        )
        user = User.objects.create_user("client1", password="pass")
        client = Client.objects.create(
            user=user, full_name="Клиент Один",
            birth_date=date(1995, 5, 5),
            phone="+375 (29) 222-22-22",
        )
        sc = ServiceCategory.objects.create(name="Уход")
        service = Service.objects.create(category=sc, name="Массаж", price=40, duration=30)
        self.appt = Appointment.objects.create(
            client=client, doctor=doctor, service=service,
            date_time=timezone.now() + timedelta(days=1),
        )

    def test_default_status(self):
        self.assertEqual(self.appt.status, "pending")

    def test_str_contains_arrow(self):
        self.assertIn("→", str(self.appt))

    def test_sale_one_to_one(self):
        sale = Sale.objects.create(appointment=self.appt, amount=40.00)
        self.assertEqual(sale.appointment, self.appt)
        self.assertEqual(self.appt.sale, sale)


# ─────────────── FORM TESTS ───────────────

class ClientRegistrationFormTest(TestCase):

    def _valid_data(self, **kwargs):
        data = {
            "username": "newuser",
            "password1": "Str0ngP@ss!",
            "password2": "Str0ngP@ss!",
            "full_name": "Новый Клиент",
            "birth_date": "1995-01-01",
            "phone": "+375 (29) 999-99-99",
            "email": "test@test.com",
            "address": "г. Минск",
        }
        data.update(kwargs)
        return data

    def test_valid_form(self):
        form = ClientRegistrationForm(data=self._valid_data())
        self.assertTrue(form.is_valid(), form.errors)

    def test_invalid_phone(self):
        form = ClientRegistrationForm(data=self._valid_data(phone="80291234567"))
        self.assertFalse(form.is_valid())
        self.assertIn("phone", form.errors)

    def test_underage_client(self):
        form = ClientRegistrationForm(data=self._valid_data(birth_date="2015-01-01"))
        self.assertFalse(form.is_valid())
        self.assertIn("birth_date", form.errors)


class ServiceFilterFormTest(TestCase):

    def test_empty_form_valid(self):
        form = ServiceFilterForm(data={})
        self.assertTrue(form.is_valid())

    def test_sort_choices(self):
        form = ServiceFilterForm(data={"sort": "price"})
        self.assertTrue(form.is_valid())


# ─────────────── VIEW TESTS ───────────────

class PublicViewTests(TestCase):

    def test_home_200(self):
        r = self.client.get("/")
        self.assertEqual(r.status_code, 200)

    def test_about_200(self):
        r = self.client.get("/about/")
        self.assertEqual(r.status_code, 200)

    def test_news_200(self):
        r = self.client.get("/news/")
        self.assertEqual(r.status_code, 200)

    def test_faq_200(self):
        r = self.client.get("/faq/")
        self.assertEqual(r.status_code, 200)

    def test_contacts_200(self):
        r = self.client.get("/contacts/")
        self.assertEqual(r.status_code, 200)

    def test_privacy_200(self):
        r = self.client.get("/privacy/")
        self.assertEqual(r.status_code, 200)

    def test_vacancies_200(self):
        r = self.client.get("/vacancies/")
        self.assertEqual(r.status_code, 200)

    def test_reviews_200(self):
        r = self.client.get("/reviews/")
        self.assertEqual(r.status_code, 200)

    def test_promos_200(self):
        r = self.client.get("/promos/")
        self.assertEqual(r.status_code, 200)

    def test_services_200(self):
        r = self.client.get("/services/")
        self.assertEqual(r.status_code, 200)

    def test_doctors_200(self):
        r = self.client.get("/doctors/")
        self.assertEqual(r.status_code, 200)

    def test_login_200(self):
        r = self.client.get("/login/")
        self.assertEqual(r.status_code, 200)

    def test_register_200(self):
        r = self.client.get("/register/client/")
        self.assertEqual(r.status_code, 200)


class AuthViewTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user("auth_user", password="pass12345")
        self.client_obj = Client.objects.create(
            user=self.user, full_name="Auth User",
            birth_date=date(1990, 1, 1),
            phone="+375 (29) 300-00-03",
        )

    def test_profile_requires_login(self):
        r = self.client.get("/profile/")
        self.assertRedirects(r, "/login/?next=/profile/", fetch_redirect_response=False)

    def test_profile_logged_in(self):
        self.client.login(username="auth_user", password="pass12345")
        r = self.client.get("/profile/")
        self.assertEqual(r.status_code, 200)

    def test_create_appointment_requires_login(self):
        r = self.client.get("/appointment/create/")
        self.assertEqual(r.status_code, 302)

    def test_statistics_requires_staff(self):
        self.client.login(username="auth_user", password="pass12345")
        r = self.client.get("/statistics/")
        self.assertEqual(r.status_code, 302)


class AppointmentCRUDTest(TestCase):

    def setUp(self):
        cat = DoctorCategory.objects.create(name="Косметология")
        self.doctor = Doctor.objects.create(
            full_name="Врач Тест", birth_date=date(1980, 1, 1),
            category=cat, specialization="Косметолог",
            phone="+375 (29) 400-00-04",
        )
        sc = ServiceCategory.objects.create(name="Уход")
        self.service = Service.objects.create(category=sc, name="Пилинг", price=60, duration=45)
        self.user = User.objects.create_user("crud_user", password="pass12345")
        self.client_obj = Client.objects.create(
            user=self.user, full_name="CRUD Клиент",
            birth_date=date(1992, 3, 3),
            phone="+375 (29) 500-00-05",
        )
        self.tc = TestClient()
        self.tc.login(username="crud_user", password="pass12345")

    def test_create_appointment(self):
        dt = (timezone.now() + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M")
        r = self.tc.post("/appointment/create/", {
            "doctor": self.doctor.pk,
            "service": self.service.pk,
            "date_time": dt,
            "notes": "",
        })
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Appointment.objects.filter(client=self.client_obj).count(), 1)

    def test_update_appointment(self):
        appt = Appointment.objects.create(
            client=self.client_obj, doctor=self.doctor, service=self.service,
            date_time=timezone.now() + timedelta(days=3),
        )
        r = self.tc.post(f"/appointment/{appt.pk}/edit/", {
            "status": "confirmed", "notes": "Подтверждено"
        })
        self.assertEqual(r.status_code, 302)
        appt.refresh_from_db()
        self.assertEqual(appt.status, "confirmed")

    def test_delete_appointment(self):
        appt = Appointment.objects.create(
            client=self.client_obj, doctor=self.doctor, service=self.service,
            date_time=timezone.now() + timedelta(days=3),
        )
        pk = appt.pk
        r = self.tc.post(f"/appointment/{pk}/delete/")
        self.assertEqual(r.status_code, 302)
        self.assertFalse(Appointment.objects.filter(pk=pk).exists())


class NewsDetailTest(TestCase):

    def setUp(self):
        self.article = Article.objects.create(
            title="Тест новость", summary="Краткое", content="Полный текст"
        )

    def test_news_detail_200(self):
        r = self.client.get(f"/news/{self.article.pk}/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Тест новость")

    def test_news_detail_404_for_unpublished(self):
        self.article.is_published = False
        self.article.save()
        r = self.client.get(f"/news/{self.article.pk}/")
        self.assertEqual(r.status_code, 404)


class ServiceFilterTest(TestCase):

    def setUp(self):
        sc = ServiceCategory.objects.create(name="Лазер")
        Service.objects.create(category=sc, name="Лазерная эпиляция", price=120, duration=60)
        Service.objects.create(category=sc, name="Фотоомоложение", price=80, duration=45)

    def test_filter_by_min_price(self):
        r = self.client.get("/services/?min_price=100")
        self.assertContains(r, "Лазерная эпиляция")
        self.assertNotContains(r, "Фотоомоложение")

    def test_search(self):
        r = self.client.get("/services/?search=Фото")
        self.assertContains(r, "Фотоомоложение")
        self.assertNotContains(r, "Лазерная эпиляция")


class ReviewTest(TestCase):

    def setUp(self):
        user = User.objects.create_user("rev_user", password="pass12345")
        self.client_obj = Client.objects.create(
            user=user, full_name="Ревьюер",
            birth_date=date(1991, 4, 4),
            phone="+375 (29) 600-00-06",
        )
        self.tc = TestClient()
        self.tc.login(username="rev_user", password="pass12345")

    def test_add_review(self):
        r = self.tc.post("/reviews/add/", {"rating": 5, "text": "Отличный центр!"})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Review.objects.filter(client=self.client_obj).count(), 1)


# ─────────────── URL TESTS ───────────────

class URLTests(TestCase):

    def test_re_path_news_detail_digit(self):
        r = self.client.get("/news/999/")
        self.assertEqual(r.status_code, 404)  # не 500, объект просто не найден

    def test_re_path_doctor_detail_digit(self):
        r = self.client.get("/doctors/999/")
        self.assertEqual(r.status_code, 404)

    def test_re_path_appointment_edit_digit(self):
        r = self.client.get("/appointment/999/edit/")
        self.assertEqual(r.status_code, 302)  # редирект на логин

    def test_url_services(self):
        from django.urls import resolve
        match = resolve("/services/")
        self.assertEqual(match.url_name, "services")


class AdminStatisticsTest(TestCase):

    def setUp(self):
        self.staff = User.objects.create_user("admin_s", password="pass12345", is_staff=True)

    def test_statistics_for_staff(self):
        self.client.login(username="admin_s", password="pass12345")
        r = self.client.get("/statistics/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Статистика")
