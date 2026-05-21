import re
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date


def validate_phone_by(value):
    pattern = r'^\+375 \(\d{2}\) \d{3}-\d{2}-\d{2}$'
    if not re.match(pattern, value):
        raise ValidationError('Телефон должен быть в формате +375 (29) XXX-XX-XX')


def validate_adult(birth_date):
    today = date.today()
    age = today.year - birth_date.year - (
        (today.month, today.day) < (birth_date.month, birth_date.day)
    )
    if age < 18:
        raise ValidationError('Возраст должен быть не менее 18 лет.')


class DoctorCategory(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название категории')
    description = models.TextField(blank=True, verbose_name='Описание')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Категория врача'
        verbose_name_plural = 'Категории врачей'


class ServiceCategory(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название категории')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Категория услуги'
        verbose_name_plural = 'Категории услуг'


class Service(models.Model):
    category = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE, verbose_name='Категория')
    name = models.CharField(max_length=200, verbose_name='Название услуги')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена')
    duration = models.PositiveIntegerField(default=30, verbose_name='Длительность (мин)')
    description = models.TextField(blank=True, verbose_name='Описание')
    is_active = models.BooleanField(default=True, verbose_name='Активна')

    def __str__(self):
        return f'{self.name} — {self.price} руб.'

    class Meta:
        verbose_name = 'Услуга'
        verbose_name_plural = 'Услуги'


class Cabinet(models.Model):
    number = models.CharField(max_length=10, unique=True, verbose_name='Номер кабинета')
    name = models.CharField(max_length=100, verbose_name='Название')

    def __str__(self):
        return f'Кабинет {self.number} — {self.name}'

    class Meta:
        verbose_name = 'Кабинет'
        verbose_name_plural = 'Кабинеты'


class Doctor(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE,
        related_name='doctor_profile', null=True, blank=True
    )
    full_name = models.CharField(max_length=200, verbose_name='ФИО')
    birth_date = models.DateField(verbose_name='Дата рождения', validators=[validate_adult])
    category = models.ForeignKey(DoctorCategory, on_delete=models.PROTECT, verbose_name='Категория')
    specialization = models.CharField(max_length=150, verbose_name='Специализация')
    phone = models.CharField(max_length=20, verbose_name='Телефон', validators=[validate_phone_by])
    experience = models.PositiveIntegerField(default=0, verbose_name='Стаж (лет)')
    photo = models.ImageField(upload_to='doctors/', blank=True, null=True, verbose_name='Фото')
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    services = models.ManyToManyField(Service, blank=True, verbose_name='Оказываемые услуги', related_name='doctors')

    def __str__(self):
        return self.full_name

    @property
    def age(self):
        today = date.today()
        return today.year - self.birth_date.year - (
            (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
        )

    class Meta:
        verbose_name = 'Врач'
        verbose_name_plural = 'Врачи'


class Client(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE,
        related_name='client_profile', null=True, blank=True
    )
    full_name = models.CharField(max_length=200, verbose_name='ФИО')
    birth_date = models.DateField(verbose_name='Дата рождения', validators=[validate_adult])
    phone = models.CharField(max_length=20, verbose_name='Телефон', validators=[validate_phone_by])
    email = models.EmailField(blank=True, verbose_name='Email')
    address = models.TextField(blank=True, verbose_name='Адрес')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name

    @property
    def age(self):
        today = date.today()
        return today.year - self.birth_date.year - (
            (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
        )

    class Meta:
        verbose_name = 'Клиент'
        verbose_name_plural = 'Клиенты'


class Schedule(models.Model):
    WEEKDAY_CHOICES = [
        (0, 'Понедельник'), (1, 'Вторник'), (2, 'Среда'),
        (3, 'Четверг'), (4, 'Пятница'), (5, 'Суббота'), (6, 'Воскресенье'),
    ]
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='schedules', verbose_name='Врач')
    cabinet = models.ForeignKey(Cabinet, on_delete=models.SET_NULL, null=True, verbose_name='Кабинет')
    weekday = models.IntegerField(choices=WEEKDAY_CHOICES, verbose_name='День недели')
    time_start = models.TimeField(verbose_name='Начало')
    time_end = models.TimeField(verbose_name='Конец')

    def __str__(self):
        return f'{self.doctor} | {self.get_weekday_display()} {self.time_start}–{self.time_end}'

    class Meta:
        verbose_name = 'Расписание'
        verbose_name_plural = 'Расписание'
        ordering = ['weekday', 'time_start']


class Appointment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидается'),
        ('confirmed', 'Подтверждено'),
        ('completed', 'Завершено'),
        ('cancelled', 'Отменено'),
    ]
    client = models.ForeignKey(Client, on_delete=models.CASCADE, verbose_name='Клиент')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, verbose_name='Врач')
    service = models.ForeignKey(Service, on_delete=models.CASCADE, verbose_name='Услуга')
    cabinet = models.ForeignKey(Cabinet, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Кабинет')
    date_time = models.DateTimeField(verbose_name='Дата и время')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='Статус')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True, verbose_name='Примечания')

    def __str__(self):
        return f'{self.client} → {self.doctor} | {self.date_time.strftime("%d/%m/%Y %H:%M")}' 

    class Meta:
        verbose_name = 'Запись'
        verbose_name_plural = 'Записи'
        ordering = ['-date_time']


class Sale(models.Model):
    appointment = models.OneToOneField(
        Appointment, on_delete=models.CASCADE, related_name='sale', verbose_name='Запись'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Сумма оплаты')
    paid_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата оплаты')
    payment_method = models.CharField(
        max_length=50, default='cash',
        choices=[('cash', 'Наличные'), ('card', 'Карта')],
        verbose_name='Способ оплаты'
    )

    def __str__(self):
        return f'Оплата {self.amount} руб. | {self.paid_at.strftime("%d/%m/%Y")}'

    class Meta:
        verbose_name = 'Продажа'
        verbose_name_plural = 'Продажи'


class Promo(models.Model):
    code = models.CharField(max_length=50, unique=True, verbose_name='Промокод')
    description = models.TextField(blank=True, verbose_name='Описание')
    discount_percent = models.PositiveIntegerField(default=0, verbose_name='Скидка %')
    valid_from = models.DateField(verbose_name='Действует с')
    valid_to = models.DateField(verbose_name='Действует до')
    is_active = models.BooleanField(default=True, verbose_name='Активен')

    def __str__(self):
        return f'{self.code} ({self.discount_percent}%)' 

    @property
    def is_current(self):
        today = date.today()
        return self.is_active and self.valid_from <= today <= self.valid_to

    class Meta:
        verbose_name = 'Промокод'
        verbose_name_plural = 'Промокоды и купоны'


class Article(models.Model):
    title = models.CharField(max_length=300, verbose_name='Заголовок')
    summary = models.TextField(verbose_name='Краткое содержание')
    content = models.TextField(verbose_name='Полный текст')
    image = models.ImageField(upload_to='articles/', blank=True, null=True, verbose_name='Картинка')
    published_at = models.DateTimeField(default=timezone.now, verbose_name='Дата публикации')
    is_published = models.BooleanField(default=True, verbose_name='Опубликована')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Статья'
        verbose_name_plural = 'Новости / Статьи'
        ordering = ['-published_at']


class FAQ(models.Model):
    question = models.CharField(max_length=300, verbose_name='Вопрос')
    answer = models.TextField(verbose_name='Ответ')
    added_at = models.DateField(auto_now_add=True, verbose_name='Дата добавления')

    def __str__(self):
        return self.question

    class Meta:
        verbose_name = 'Вопрос-ответ'
        verbose_name_plural = 'Словарь терминов / FAQ'
        ordering = ['-added_at']


class Contact(models.Model):
    full_name = models.CharField(max_length=200, verbose_name='ФИО сотрудника')
    position = models.CharField(max_length=150, verbose_name='Должность')
    phone = models.CharField(max_length=20, verbose_name='Телефон')
    email = models.EmailField(blank=True, verbose_name='Email')
    photo = models.ImageField(upload_to='contacts/', blank=True, null=True, verbose_name='Фото')
    description = models.TextField(blank=True, verbose_name='Описание работ')

    def __str__(self):
        return self.full_name

    class Meta:
        verbose_name = 'Контакт'
        verbose_name_plural = 'Контакты сотрудников'


class Vacancy(models.Model):
    title = models.CharField(max_length=200, verbose_name='Должность')
    description = models.TextField(verbose_name='Описание')
    salary = models.CharField(max_length=100, blank=True, verbose_name='Зарплата')
    is_open = models.BooleanField(default=True, verbose_name='Открыта')
    created_at = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Вакансия'
        verbose_name_plural = 'Вакансии'


class Review(models.Model):
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='reviews', verbose_name='Клиент')
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES, verbose_name='Оценка')
    text = models.TextField(verbose_name='Текст отзыва')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата')
    is_approved = models.BooleanField(default=True, verbose_name='Одобрен')

    def __str__(self):
        return f'{self.client} | {self.rating}*'

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        ordering = ['-created_at']


class CompanyInfo(models.Model):
    name = models.CharField(max_length=200, verbose_name='Название компании')
    description = models.TextField(verbose_name='Описание')
    founded_year = models.PositiveIntegerField(blank=True, null=True, verbose_name='Год основания')
    logo = models.ImageField(upload_to='company/', blank=True, null=True, verbose_name='Логотип')
    video_url = models.URLField(blank=True, verbose_name='Ссылка на видео')
    requisites = models.TextField(blank=True, verbose_name='Реквизиты')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'О компании'
        verbose_name_plural = 'О компании'
