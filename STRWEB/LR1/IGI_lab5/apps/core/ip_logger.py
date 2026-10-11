import requests
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_ip_info(ip):
    cache_key = f"ipinfo_{ip}"
    data = cache.get(cache_key)

    if data:
        return data

    try:
        resp = requests.get(f"https://ipapi.co/{ip}/json/", timeout=6)
        if resp.status_code == 200:
            info = resp.json()
            result = {
                'ip': ip,
                'country': info.get('country_name'),
                'city': info.get('city'),
                'region': info.get('region'),
                'isp': info.get('org'),
                'timezone': info.get('timezone'),
            }
            cache.set(cache_key, result, 3600 * 12)  # кэш на 12 часов
            return result
    except Exception as e:
        logger.error(f"Ошибка получения info по IP {ip}: {e}")

    return {'ip': ip, 'error': 'Не удалось получить информацию'}