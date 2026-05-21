from .currency import get_exchange_rates


def currency_context(request):
    current_currency = request.session.get('currency', 'BYN')

    return {
        'currencies': {
            'BYN': 'BYN',
            'USD': 'USD',
            'RUB': 'RUB',
        },
        'current_currency': current_currency,
        'exchange_rates': get_exchange_rates(),
    }