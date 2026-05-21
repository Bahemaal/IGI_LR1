from django.urls import path, re_path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # ── Главная ──
    path('', views.home, name='home'),

    # ── Публичные страницы ──
    path('about/', views.about, name='about'),
    path('news/', views.news, name='news'),
    # re_path: pk — только цифры
    re_path(r'^news/(?P<pk>\d+)/$', views.news_detail, name='news_detail'),
    path('faq/', views.faq_view, name='faq'),
    path('contacts/', views.contacts_view, name='contacts'),
    path('privacy/', views.privacy_view, name='privacy'),
    path('vacancies/', views.vacancies_view, name='vacancies'),
    path('reviews/', views.reviews_view, name='reviews'),
    path('reviews/add/', views.add_review, name='add_review'),
    path('promos/', views.promos_view, name='promos'),

    # ── Врачи и услуги ──
    path('doctors/', views.doctors_list, name='doctors'),
    # re_path: pk — только цифры
    re_path(r'^doctors/(?P<pk>\d+)/$', views.doctor_detail, name='doctor_detail'),
    path('services/', views.services_list, name='services'),

    # ── Авторизация ──
    path('register/client/', views.register_client, name='register_client'),
    path('login/', views.user_login, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),

    # ── Записи: CRUD ──
    path('appointment/create/', views.create_appointment, name='create_appointment'),
    # re_path для update и delete
    re_path(r'^appointment/(?P<pk>\d+)/edit/$', views.update_appointment, name='update_appointment'),
    re_path(r'^appointment/(?P<pk>\d+)/delete/$', views.delete_appointment, name='delete_appointment'),

    # ── Личные кабинеты ──
    path('profile/', views.profile, name='profile'),
    path('doctor/profile/', views.doctor_profile, name='doctor_profile'),

    # ── Статистика (staff only) ──
    path('statistics/', views.admin_statistics, name='admin_statistics'),
]