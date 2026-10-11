# Generated manually for CompanyHistoryEvent and Certificate models

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_order_orderitem'),
    ]

    operations = [
        migrations.CreateModel(
            name='CompanyHistoryEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year', models.PositiveIntegerField(verbose_name='Год')),
                ('title', models.CharField(max_length=200, verbose_name='Событие')),
                ('description', models.TextField(blank=True, verbose_name='Описание')),
            ],
            options={
                'verbose_name': 'Событие истории компании',
                'verbose_name_plural': 'История компании',
                'ordering': ['year'],
            },
        ),
        migrations.CreateModel(
            name='Certificate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='Название')),
                ('image', models.ImageField(upload_to='certificates/', verbose_name='Скан/фото сертификата')),
                ('issued_year', models.PositiveIntegerField(blank=True, null=True, verbose_name='Год выдачи')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='Порядок показа')),
            ],
            options={
                'verbose_name': 'Сертификат',
                'verbose_name_plural': 'Сертификаты',
                'ordering': ['order'],
            },
        ),
    ]
