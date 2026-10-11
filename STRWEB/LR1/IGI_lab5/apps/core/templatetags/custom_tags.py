from django import template
from ..currency import get_exchange_rates
import os

register = template.Library()

@register.filter
def convert_price(price, currency='BYN'):
    """Конвертирует цену из BYN в выбранную валюту"""
    if price in (None, '', 'None', 'null'):
        return 0.00

    try:
        price_float = float(price)
    except (ValueError, TypeError):
        return 0.00

    try:
        rates = get_exchange_rates()
        byn_rate = rates.get('BYN', 1.0)
        target_rate = rates.get(currency, 1.0)

        if byn_rate == 0:
            return price_float

        converted = price_float / target_rate * byn_rate
        return round(converted, 2)
    except Exception:
        # Если что-то пошло не так — возвращаем оригинальную цену
        return round(price_float, 2)


@register.filter
def thumb_url(image_field):
    """
    Для адаптивных изображений (srcset): возвращает URL уменьшенной версии
    файла (имя_small.ext), если она была сгенерирована рядом с оригиналом.
    Если уменьшенной версии нет — возвращает исходный URL.
    """
    if not image_field:
        return ""
    try:
        url = image_field.url
        path = image_field.path
    except (ValueError, AttributeError):
        return ""
    name, ext = os.path.splitext(path)
    small_path = f"{name}_small{ext}"
    if os.path.exists(small_path):
        url_name, url_ext = os.path.splitext(url)
        return f"{url_name}_small{url_ext}"
    return url