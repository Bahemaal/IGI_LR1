import requests
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)


def get_exchange_rates():
    rates = cache.get('nbrb_rates')
    if rates:
        return rates

    try:
        resp = requests.get('https://api.nbrb.by/exrates/rates?periodicity=0', timeout=5)
        resp.raise_for_status()
        data = resp.json()

        rates = {'BYN': 1.0}
        for item in data:
            code = item['Cur_Abbreviation']
            if code in ['USD']:
                rates[code] = float(item['Cur_OfficialRate'])
            elif code in ['RUB']:
                rates[code] = float(item['Cur_OfficialRate'])/100

        cache.set('nbrb_rates', rates, 3600)
        return rates
    except Exception as e:
        logger.error(f"Ошибка с курсами: {e}")
        return {'BYN': 1.0, 'USD': 3.2, 'RUB': 0.035}