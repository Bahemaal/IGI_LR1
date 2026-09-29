import logging
import calendar
from statistics import mean, median, mode, StatisticsError
from datetime import date

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login as auth_login
from django.contrib import messages
from django.db.models import Count, Sum, Q
from django.utils import timezone

from .forms import (
    ClientRegistrationForm, AppointmentForm,
    AppointmentUpdateForm, ReviewForm, ServiceFilterForm, CheckoutForm
)
from .models import (
    Doctor, Service, Appointment, Client, ServiceCategory,
    Article, FAQ, Contact, Vacancy, Review, Promo, Schedule,
    Sale, CompanyInfo, Cabinet, Banner, Partner, Order, OrderItem,
    CompanyHistoryEvent, Certificate
)
from .cart import Cart

logger = logging.getLogger(__name__)


# ─────────── ПУБЛИЧНЫЕ СТРАНИЦЫ ────────────

def home(request):
    latest_article = Article.objects.filter(is_published=True).first()
    doctors = Doctor.objects.filter(is_active=True)[:6]
    services = Service.objects.filter(is_active=True)[:8]
    banners = Banner.objects.filter(is_active=True)
    partners = Partner.objects.filter(is_active=True)
    company = CompanyInfo.objects.first()
    now = timezone.now()
    user_tz = timezone.get_current_timezone()
    cal_text = calendar.month(now.year, now.month)
    context = {
        "latest_article": latest_article,
        "doctors": doctors,
        "services": services,
        "banners": banners,
        "partners": partners,
        "company": company,
        "now_local": now,
        "cal_text": cal_text,
        "user_tz": user_tz,
    }
    logger.info("Home page requested")
    return render(request, "home.html", context)


def about(request):
    company = CompanyInfo.objects.first()
    history = CompanyHistoryEvent.objects.all()
    certificates = Certificate.objects.all()
    video_embed_url = None
    if company and company.video_url:
        url = company.video_url
        if "youtu.be/" in url:
            vid = url.split("youtu.be/")[-1].split("?")[0]
            video_embed_url = f"https://www.youtube-nocookie.com/embed/{vid}"
        elif "watch?v=" in url:
            vid = url.split("watch?v=")[-1].split("&")[0]
            video_embed_url = f"https://www.youtube-nocookie.com/embed/{vid}"
        elif "youtube.com/embed/" in url or "youtube-nocookie.com/embed/" in url:
            video_embed_url = url.replace("www.youtube.com", "www.youtube-nocookie.com")
    return render(request, "about.html", {
        "company": company, "history": history, "certificates": certificates,
        "video_embed_url": video_embed_url,
    })


def news(request):
    articles = Article.objects.filter(is_published=True)
    return render(request, "news.html", {"articles": articles})


def news_detail(request, pk):
    article = get_object_or_404(Article, pk=pk, is_published=True)
    return render(request, "news_detail.html", {"article": article})


def faq_view(request):
    items = FAQ.objects.all()
    return render(request, "faq.html", {"items": items})


def contacts_view(request):
    contacts = Contact.objects.all()
    return render(request, "contacts.html", {"contacts": contacts})


def privacy_view(request):
    return render(request, "privacy.html")


def vacancies_view(request):
    vacancies = Vacancy.objects.filter(is_open=True)
    return render(request, "vacancies.html", {"vacancies": vacancies})


def reviews_view(request):
    reviews = Review.objects.filter(is_approved=True)
    form = None
    if request.user.is_authenticated and hasattr(request.user, "client_profile"):
        form = ReviewForm()
    return render(request, "reviews.html", {"reviews": reviews, "form": form})


@login_required
def add_review(request):
    if not hasattr(request.user, "client_profile"):
        messages.error(request, "Только клиенты могут оставлять отзывы.")
        return redirect("reviews")
    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.client = request.user.client_profile
            review.save()
            messages.success(request, "Отзыв добавлен!")
            logger.info("New review by client %s", request.user.client_profile)
        else:
            messages.error(request, "Проверьте форму.")
    return redirect("reviews")


def promos_view(request):
    today = date.today()
    current = Promo.objects.filter(is_active=True, valid_from__lte=today, valid_to__gte=today)
    archived = Promo.objects.filter(is_active=True, valid_to__lt=today)
    return render(request, "promos.html", {"current": current, "archived": archived})


# ─────────── УСЛУГИ ────────────

def services_list(request):
    qs = Service.objects.filter(is_active=True).select_related("category")
    form = ServiceFilterForm(request.GET)

    if form.is_valid():
        cat = form.cleaned_data.get("category")
        min_p = form.cleaned_data.get("min_price")
        max_p = form.cleaned_data.get("max_price")
        search = form.cleaned_data.get("search")
        sort = form.cleaned_data.get("sort") or "name"
        if cat:
            qs = qs.filter(category=cat)
        if min_p is not None:
            qs = qs.filter(price__gte=min_p)
        if max_p is not None:
            qs = qs.filter(price__lte=max_p)
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(description__icontains=search))
        qs = qs.order_by(sort)

    return render(request, "services.html", {
        "services": qs, "form": form,
        "all_service_names": Service.objects.filter(is_active=True).values_list("name", flat=True),
    })


def service_detail(request, pk):
    service = get_object_or_404(Service, pk=pk, is_active=True)
    related = Service.objects.filter(category=service.category, is_active=True).exclude(pk=pk)[:4]
    doctors = service.doctors.filter(is_active=True)
    return render(request, "service_detail.html", {
        "service": service, "related": related, "doctors": doctors,
    })


# ─────────── КОРЗИНА ────────────

def cart_view(request):
    cart = Cart(request)
    return render(request, "cart.html", {"cart_items": cart.get_items(), "cart_total": cart.get_total()})


def cart_add(request, pk):
    service = get_object_or_404(Service, pk=pk, is_active=True)
    cart = Cart(request)
    quantity = 1
    if request.method == "POST":
        try:
            quantity = max(1, int(request.POST.get("quantity", 1)))
        except (TypeError, ValueError):
            quantity = 1
    cart.add(service, quantity)
    messages.success(request, f'«{service.name}» добавлена в корзину.')
    return redirect(request.POST.get("next") or "cart")


def cart_update(request, pk):
    if request.method == "POST":
        try:
            quantity = int(request.POST.get("quantity", 1))
        except (TypeError, ValueError):
            quantity = 1
        Cart(request).update(pk, quantity)
    return redirect("cart")


def cart_remove(request, pk):
    Cart(request).remove(pk)
    messages.info(request, "Позиция удалена из корзины.")
    return redirect("cart")


def checkout_view(request):
    cart = Cart(request)
    if len(cart) == 0:
        messages.warning(request, "Ваша корзина пуста.")
        return redirect("services")

    items = cart.get_items()
    subtotal = cart.get_total()

    initial = {}
    client = None
    if request.user.is_authenticated and hasattr(request.user, "client_profile"):
        client = request.user.client_profile
        initial = {
            "full_name": client.full_name,
            "phone": client.phone,
            "email": client.email,
            "address": client.address,
        }

    total = subtotal

    if request.method == "POST":
        form = CheckoutForm(request.POST, initial=initial)
        if form.is_valid():
            promo = form.cleaned_data.get("promo_code")
            if promo:
                total = subtotal * (1 - promo.discount_percent / 100)
            else:
                total = subtotal

            order = Order.objects.create(
                client=client,
                full_name=form.cleaned_data["full_name"],
                phone=form.cleaned_data["phone"],
                email=form.cleaned_data["email"],
                address=form.cleaned_data["address"],
                promo=promo,
                payment_method=form.cleaned_data["payment_method"],
                total_amount=total,
                status="paid",
            )
            for item in items:
                OrderItem.objects.create(
                    order=order,
                    service=item["service"],
                    quantity=item["quantity"],
                    price=item["service"].price,
                )
            cart.clear()
            logger.info("New order #%d created for %s", order.pk, order.full_name)
            return redirect("order_success", pk=order.pk)
    else:
        form = CheckoutForm(initial=initial)

    return render(request, "checkout.html", {
        "form": form, "cart_items": items, "cart_total": subtotal,
    })


def order_success(request, pk):
    order = get_object_or_404(Order, pk=pk)
    return render(request, "order_success.html", {"order": order})


# ─────────── ВРАЧИ ────────────

def doctors_list(request):
    q = request.GET.get("q", "")
    sort = request.GET.get("sort", "full_name")
    doctors = Doctor.objects.filter(is_active=True).select_related("category")
    if q:
        doctors = doctors.filter(
            Q(full_name__icontains=q) | Q(specialization__icontains=q)
        )
    if sort in ("full_name", "experience", "-experience"):
        doctors = doctors.order_by(sort)
    return render(request, "doctors.html", {"doctors": doctors, "q": q})


def doctor_detail(request, pk):
    doctor = get_object_or_404(Doctor, pk=pk, is_active=True)
    schedules = doctor.schedules.all()
    return render(request, "doctor_detail.html", {"doctor": doctor, "schedules": schedules})


# ─────────── АВТОРИЗАЦИЯ ────────────

def register_client(request):
    if request.method == "POST":
        form = ClientRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            Client.objects.create(
                user=user,
                full_name=form.cleaned_data["full_name"],
                birth_date=form.cleaned_data["birth_date"],
                phone=form.cleaned_data["phone"],
                email=form.cleaned_data["email"],
                address=form.cleaned_data.get("address", ""),
            )
            login(request, user)
            logger.info("New client registered: %s", user.username)
            return redirect("home")
    else:
        form = ClientRegistrationForm()
    return render(request, "register_client.html", {"form": form})


def user_login(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            auth_login(request, form.get_user())
            return redirect("home")
    else:
        form = AuthenticationForm()
    return render(request, "login.html", {"form": form})


# ─────────── ЛИЧНЫЙ КАБИНЕТ КЛИЕНТА ────────────

@login_required
def profile(request):
    if not hasattr(request.user, "client_profile"):
        messages.warning(request, "Ваш профиль не найден.")
        return redirect("home")

    client = request.user.client_profile
    appointments = Appointment.objects.filter(client=client).order_by("-date_time")

    # === IP ИНФО ===
    from .ip_logger import get_client_ip, get_ip_info
    ip = get_client_ip(request)
    ip_info = get_ip_info(ip)

    context = {
        'appointments': appointments,
        'total_appointments': appointments.count(),
        'upcoming': appointments.filter(date_time__gte=timezone.now()).count(),
        'completed': appointments.filter(status='completed').count(),
        'client': client,
        'ip': ip,
        'ip_info': ip_info,
    }
    return render(request, 'profile.html', context)


# ─────────── ЗАПИСИ CRUD ────────────

@login_required
def create_appointment(request):
    if not hasattr(request.user, "client_profile"):
        messages.error(request, "Зарегистрируйтесь как клиент.")
        return redirect("register_client")
    if request.method == "POST":
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appt = form.save(commit=False)
            appt.client = request.user.client_profile
            appt.save()
            messages.success(request, "Запись создана!")
            logger.info("Appointment created by %s", request.user.username)
            return redirect("profile")
    else:
        form = AppointmentForm()
    return render(request, "create_appointment.html", {"form": form})


@login_required
def update_appointment(request, pk):
    appt = get_object_or_404(Appointment, pk=pk)
    if not request.user.is_staff:
        if hasattr(request.user, "client_profile") and appt.client != request.user.client_profile:
            messages.error(request, "Нет доступа.")
            return redirect("profile")
        if hasattr(request.user, "doctor_profile") and appt.doctor != request.user.doctor_profile:
            messages.error(request, "Нет доступа.")
            return redirect("doctor_profile")
    if request.method == "POST":
        form = AppointmentUpdateForm(request.POST, instance=appt)
        if form.is_valid():
            form.save()
            messages.success(request, "Запись обновлена!")
            logger.info("Appointment %d updated by %s", pk, request.user.username)
            return redirect("profile")
    else:
        form = AppointmentUpdateForm(instance=appt)
    return render(request, "update_appointment.html", {"form": form, "appt": appt})


@login_required
def delete_appointment(request, pk):
    appt = get_object_or_404(Appointment, pk=pk)
    if not request.user.is_staff:
        if hasattr(request.user, "client_profile") and appt.client != request.user.client_profile:
            messages.error(request, "Нет доступа.")
            return redirect("profile")
    if request.method == "POST":
        appt.delete()
        messages.success(request, "Запись отменена.")
        logger.info("Appointment %d deleted by %s", pk, request.user.username)
        return redirect("profile")
    return render(request, "delete_appointment.html", {"appt": appt})


# ─────────── КАБИНЕТ ВРАЧА ────────────

@login_required
def doctor_profile(request):
    if not hasattr(request.user, "doctor_profile"):
        messages.error(request, "Нет доступа.")
        return redirect("home")
    doctor = request.user.doctor_profile
    appointments = Appointment.objects.filter(doctor=doctor).order_by("-date_time")
    schedules = doctor.schedules.all()
    return render(request, "doctor_profile.html", {
        "doctor": doctor, "appointments": appointments, "schedules": schedules
    })


# ─────────── СТАТИСТИКА ────────────

@staff_member_required
def admin_statistics(request):
    total_appointments = Appointment.objects.count()
    completed = Appointment.objects.filter(status="completed").count()
    upcoming = Appointment.objects.filter(date_time__gte=timezone.now()).count()

    popular_services = Service.objects.annotate(
        appointment_count=Count("appointment")
    ).order_by("-appointment_count")[:5]

    revenue = Sale.objects.aggregate(total=Sum("amount"))["total"] or 0

    prices = list(Service.objects.values_list("price", flat=True))
    price_mean = round(float(mean(prices)), 2) if prices else 0
    price_median = round(float(median(prices)), 2) if prices else 0
    try:
        price_mode = round(float(mode(prices)), 2)
    except StatisticsError:
        price_mode = "—"

    today = date.today()
    ages = [
        today.year - c.birth_date.year - (
            (today.month, today.day) < (c.birth_date.month, c.birth_date.day)
        )
        for c in Client.objects.all()
    ]
    age_mean = round(mean(ages), 1) if ages else 0
    age_median = round(median(ages), 1) if ages else 0

    chart_data = list(
        ServiceCategory.objects.annotate(cnt=Count("service")).values("name", "cnt")
    )
    chart_labels = str([d["name"] for d in chart_data])
    chart_values = str([d["cnt"] for d in chart_data])

    context = {
        "total_appointments": total_appointments,
        "completed": completed,
        "upcoming": upcoming,
        "popular_services": popular_services,
        "revenue": revenue,
        "price_mean": price_mean,
        "price_median": price_median,
        "price_mode": price_mode,
        "age_mean": age_mean,
        "age_median": age_median,
        "chart_labels": chart_labels,
        "chart_values": chart_values,
        "clients_alpha": Client.objects.order_by("full_name"),
    }
    return render(request, "admin_statistics.html", context)


from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json


@csrf_exempt  # важно, потому что fetch шлёт JSON
def set_currency(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            currency = data.get('currency', 'BYN')
            if currency in ['BYN', 'USD', 'RUB']:
                request.session['currency'] = currency
                return JsonResponse({'status': 'ok', 'currency': currency})
        except:
            pass

    return JsonResponse({'status': 'error'}, status=400)


