from django import template
from ..currency import get_exchange_rates

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