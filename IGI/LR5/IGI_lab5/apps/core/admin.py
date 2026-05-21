from django.contrib import admin
from .models import (
    DoctorCategory, Doctor, Client, ServiceCategory,
    Service, Cabinet, Appointment, Sale, Schedule,
    Promo, Article, FAQ, Contact, Vacancy, Review, CompanyInfo
)


class ScheduleInline(admin.TabularInline):
    model = Schedule
    extra = 1


@admin.register(DoctorCategory)
class DoctorCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'category', 'specialization', 'experience', 'phone', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('full_name', 'specialization', 'phone')
    raw_id_fields = ('user',)
    filter_horizontal = ('services',)
    inlines = [ScheduleInline]


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'birth_date', 'get_age', 'phone', 'email')
    list_filter = ('birth_date',)
    search_fields = ('full_name', 'phone', 'email')
    raw_id_fields = ('user',)

    @admin.display(description='Возраст')
    def get_age(self, obj):
        return obj.age


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'duration', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'description')
    list_editable = ('is_active',)


@admin.register(Cabinet)
class CabinetAdmin(admin.ModelAdmin):
    list_display = ('number', 'name')


class SaleInline(admin.TabularInline):
    model = Sale
    extra = 0


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('client', 'doctor', 'service', 'date_time', 'status', 'cabinet')
    list_filter = ('status', 'date_time', 'doctor', 'service')
    search_fields = ('client__full_name', 'doctor__full_name', 'notes')
    date_hierarchy = 'date_time'
    raw_id_fields = ('client', 'doctor', 'service', 'cabinet')
    inlines = [SaleInline]


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('appointment', 'amount', 'paid_at', 'payment_method')
    list_filter = ('payment_method', 'paid_at')


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'weekday', 'cabinet', 'time_start', 'time_end')
    list_filter = ('weekday', 'doctor')


@admin.register(Promo)
class PromoAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_percent', 'valid_from', 'valid_to', 'is_active')
    list_filter = ('is_active',)
    list_editable = ('is_active',)


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'published_at', 'is_published')
    list_filter = ('is_published',)
    search_fields = ('title', 'summary')
    list_editable = ('is_published',)


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'added_at')
    search_fields = ('question', 'answer')


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'position', 'phone', 'email')
    search_fields = ('full_name', 'position')


@admin.register(Vacancy)
class VacancyAdmin(admin.ModelAdmin):
    list_display = ('title', 'salary', 'is_open', 'created_at')
    list_filter = ('is_open',)
    list_editable = ('is_open',)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('client', 'rating', 'created_at', 'is_approved')
    list_filter = ('rating', 'is_approved')
    list_editable = ('is_approved',)


@admin.register(CompanyInfo)
class CompanyInfoAdmin(admin.ModelAdmin):
    list_display = ('name', 'founded_year')
