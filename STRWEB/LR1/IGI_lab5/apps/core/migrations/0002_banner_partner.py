# Generated manually for Banner and Partner models

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Banner',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='Заголовок')),
                ('image', models.ImageField(upload_to='banners/', verbose_name='Изображение')),
                ('link', models.URLField(blank=True, verbose_name='Ссылка при клике')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='Порядок показа')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активен')),
            ],
            options={
                'verbose_name': 'Рекламный баннер',
                'verbose_name_plural': 'Рекламные баннеры',
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='Partner',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='Название компании')),
                ('logo', models.ImageField(upload_to='partners/', verbose_name='Логотип')),
                ('website', models.URLField(verbose_name='Сайт компании')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='Порядок показа')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активен')),
            ],
            options={
                'verbose_name': 'Партнёр',
                'verbose_name_plural': 'Партнёры',
                'ordering': ['order'],
            },
        ),
    ]
