from django.urls import path, re_path
from django.contrib.auth import views as auth_views
from . import views
from .multitasking import multitasking_view
from .views import set_currency

urlpatterns = [
    # Главная
    path("", views.home, name="home"),

    # Публичные страницы
    path("about/", views.about, name="about"),
    path("faq/", views.faq_view, name="faq"),
    path("contacts/", views.contacts_view, name="contacts"),
    path("privacy/", views.privacy_view, name="privacy"),
    path("vacancies/", views.vacancies_view, name="vacancies"),
    path("reviews/", views.reviews_view, name="reviews"),
    path("reviews/add/", views.add_review, name="add_review"),
    path("promos/", views.promos_view, name="promos"),

    # Новости  — path + re_path для detail
    path("news/", views.news, name="news"),
    re_path(r"^news/(?P<pk>[0-9]+)/$", views.news_detail, name="news_detail"),

    # Врачи — re_path для detail
    path("doctors/", views.doctors_list, name="doctors"),
    re_path(r"^doctors/(?P<pk>[0-9]+)/$", views.doctor_detail, name="doctor_detail"),

    # Услуги
    path("services/", views.services_list, name="services"),
    re_path(r"^services/(?P<pk>[0-9]+)/$", views.service_detail, name="service_detail"),

    # Корзина и оформление заказа
    path("cart/", views.cart_view, name="cart"),
    re_path(r"^cart/add/(?P<pk>[0-9]+)/$", views.cart_add, name="cart_add"),
    re_path(r"^cart/update/(?P<pk>[0-9]+)/$", views.cart_update, name="cart_update"),
    re_path(r"^cart/remove/(?P<pk>[0-9]+)/$", views.cart_remove, name="cart_remove"),
    path("checkout/", views.checkout_view, name="checkout"),
    re_path(r"^order/(?P<pk>[0-9]+)/success/$", views.order_success, name="order_success"),

    # Авторизация
    path("register/client/", views.register_client, name="register_client"),
    path("login/", views.user_login, name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="home"), name="logout"),

    # Личный кабинет клиента
    path("profile/", views.profile, name="profile"),

    # CRUD записей — re_path для edit и delete
    path("appointment/create/", views.create_appointment, name="create_appointment"),
    re_path(r"^appointment/(?P<pk>[0-9]+)/edit/$", views.update_appointment, name="update_appointment"),
    re_path(r"^appointment/(?P<pk>[0-9]+)/delete/$", views.delete_appointment, name="delete_appointment"),

    # Кабинет врача
    path("doctor/profile/", views.doctor_profile, name="doctor_profile"),

    # Многозадачность (доп. задание)
    path("multitasking/", multitasking_view, name="multitasking"),

    # Статистика (staff only)
    path("statistics/", views.admin_statistics, name="admin_statistics"),

    path('set-currency/', set_currency, name='set_currency'),
]
