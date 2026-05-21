from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.core'          # ← Вот это главное!
    verbose_name = "Косметологический центр"