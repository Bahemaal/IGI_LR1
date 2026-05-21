

from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from .forms import ClientRegistrationForm, AppointmentForm
from .models import Doctor, Service, Appointment, Client, ServiceCategory


def home(request):
    doctors = Doctor.objects.filter(is_active=True)[:6]
    services = Service.objects.all()[:8]

    greeting_name = request.user.username

    if request.user.is_authenticated and hasattr(request.user, 'client_profile'):
        greeting_name = request.user.client_profile.full_name

    context = {
        'doctors': doctors,
        'services': services,
        'greeting_name': greeting_name,
    }
    return render(request, 'home.html', context)

def register_client(request):
    if request.method == 'POST':
        form = ClientRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            Client.objects.create(
                user=user,
                full_name=form.cleaned_data['full_name'],
                birth_date=form.cleaned_data['birth_date'],
                phone=form.cleaned_data['phone'],
                email=form.cleaned_data['email'],
                address=form.cleaned_data.get('address', '')
            )
            login(request, user)
            return redirect('home')
    else:
        form = ClientRegistrationForm()

    return render(request, 'register_client.html', {'form': form})


@login_required
def create_appointment(request):
    # Проверяем, есть ли профиль клиента
    if not hasattr(request.user, 'client_profile'):
        return redirect('login')  # если нет профиля — отправляем регистрироваться

    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.client = request.user.client_profile
            appointment.save()
            return redirect('home')
    else:
        form = AppointmentForm()

    return render(request, 'create_appointment.html', {'form': form})

from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login as auth_login

def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})


@login_required
def profile(request):
    client = request.user.client_profile
    appointments = Appointment.objects.filter(client=client).order_by('-date_time')

    # Статистика для клиента
    total_appointments = appointments.count()
    upcoming = appointments.filter(date_time__gte=timezone.now()).count()
    completed = appointments.filter(status='completed').count()

    context = {
        'appointments': appointments,
        'total_appointments': total_appointments,
        'upcoming': upcoming,
        'completed': completed,
    }
    return render(request, 'profile.html', context)


from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Sum, Avg
from django.utils import timezone


@staff_member_required
def admin_statistics(request):
    # Общая статистика
    total_appointments = Appointment.objects.count()
    completed = Appointment.objects.filter(status='completed').count()
    upcoming = Appointment.objects.filter(date_time__gte=timezone.now()).count()

    # Популярные услуги
    popular_services = Service.objects.annotate(
        appointment_count=Count('appointment')
    ).order_by('-appointment_count')[:5]

    # Выручка (примерно)
    revenue = Appointment.objects.filter(status='completed').aggregate(
        total=Sum('service__price')
    )['total'] or 0

    context = {
        'total_appointments': total_appointments,
        'completed': completed,
        'upcoming': upcoming,
        'popular_services': popular_services,
        'revenue': revenue,
    }
    return render(request, 'admin_statistics.html', context)

def doctors_list(request):
    doctors = Doctor.objects.filter(is_active=True)
    context = {'doctors': doctors}
    return render(request, 'doctors.html', context)


def services_list(request):
    categories = ServiceCategory.objects.all()
    services = Service.objects.all()

    context = {
        'categories': categories,
        'services': services,
    }
    return render(request, 'services.html', context)