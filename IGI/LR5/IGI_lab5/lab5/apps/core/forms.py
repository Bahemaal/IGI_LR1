import re
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import Client, Doctor, DoctorCategory, Service, Cabinet, Appointment, Review


# ─── общий валидатор телефона для форм ───
def validate_phone_form(value):
    if not re.match(r'^\+375 \(\d{2}\) \d{3}-\d{2}-\d{2}$', value):
        raise ValidationError('Формат: +375 (29) XXX-XX-XX')


class ClientRegistrationForm(UserCreationForm):
    full_name = forms.CharField(max_length=200, label='ФИО')
    birth_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label='Дата рождения'
    )
    phone = forms.CharField(
        max_length=20, label='Телефон',
        help_text='Формат: +375 (29) XXX-XX-XX',
        widget=forms.TextInput(attrs={'placeholder': '+375 (29) XXX-XX-XX'})
    )
    email = forms.EmailField(label='Email')
    address = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False, label='Адрес'
    )

    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']

    def clean_phone(self):
        phone = self.cleaned_data['phone']
        validate_phone_form(phone)
        return phone

    def clean_birth_date(self):
        from datetime import date
        bd = self.cleaned_data['birth_date']
        today = date.today()
        age = today.year - bd.year - ((today.month, today.day) < (bd.month, bd.day))
        if age < 18:
            raise ValidationError('Возраст должен быть не менее 18 лет.')
        return bd


class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['doctor', 'service', 'cabinet', 'date_time', 'notes']
        widgets = {
            'date_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_date_time(self):
        from django.utils import timezone
        dt = self.cleaned_data['date_time']
        if dt < timezone.now():
            raise ValidationError('Дата записи не может быть в прошлом.')
        return dt


class AppointmentUpdateForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['status', 'notes']
        widgets = {'notes': forms.Textarea(attrs={'rows': 3})}


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'text']
        widgets = {'text': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Ваш отзыв...'})}
        labels = {'rating': 'Оценка (1–5)', 'text': 'Текст отзыва'}


class ServiceFilterForm(forms.Form):
    category = forms.ModelChoiceField(
        queryset=None, required=False, empty_label='Все категории', label='Категория'
    )
    min_price = forms.DecimalField(required=False, min_value=0, label='Цена от')
    max_price = forms.DecimalField(required=False, min_value=0, label='Цена до')
    search = forms.CharField(required=False, label='Поиск', max_length=200)
    sort = forms.ChoiceField(
        required=False,
        choices=[('name', 'По названию'), ('price', 'Дешевле'), ('-price', 'Дороже')],
        label='Сортировка'
    )

    def __init__(self, *args, **kwargs):
        from .models import ServiceCategory
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = ServiceCategory.objects.all()