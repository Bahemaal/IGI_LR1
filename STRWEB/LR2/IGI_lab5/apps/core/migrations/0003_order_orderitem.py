# Generated manually for Order/OrderItem models

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_banner_partner'),
    ]

    operations = [
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('full_name', models.CharField(max_length=200, verbose_name='ФИО')),
                ('phone', models.CharField(max_length=20, verbose_name='Телефон')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='Email')),
                ('address', models.TextField(blank=True, verbose_name='Адрес доставки')),
                ('payment_method', models.CharField(choices=[('card', 'Банковская карта'), ('cash', 'Наличные при визите')], default='card', max_length=20, verbose_name='Способ оплаты')),
                ('total_amount', models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Итоговая сумма')),
                ('status', models.CharField(choices=[('new', 'Новый'), ('paid', 'Оплачен'), ('cancelled', 'Отменён')], default='new', max_length=20, verbose_name='Статус')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата оформления')),
                ('client', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='orders', to='core.client', verbose_name='Клиент')),
                ('promo', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.promo', verbose_name='Промокод')),
            ],
            options={
                'verbose_name': 'Заказ',
                'verbose_name_plural': 'Заказы',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='OrderItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField(default=1, verbose_name='Количество')),
                ('price', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Цена на момент заказа')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='core.order', verbose_name='Заказ')),
                ('service', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='core.service', verbose_name='Услуга')),
            ],
            options={
                'verbose_name': 'Позиция заказа',
                'verbose_name_plural': 'Позиции заказа',
            },
        ),
    ]
