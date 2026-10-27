"""
Корзина на основе сессии Django.
Хранит { service_id (str): quantity (int) } в request.session['cart'].
"""
from decimal import Decimal
from .models import Service

CART_SESSION_KEY = "cart"


class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(CART_SESSION_KEY)
        if cart is None:
            cart = self.session[CART_SESSION_KEY] = {}
        self.cart = cart

    def add(self, service, quantity=1):
        service_id = str(service.pk)
        if service_id in self.cart:
            self.cart[service_id] += quantity
        else:
            self.cart[service_id] = quantity
        if self.cart[service_id] < 1:
            self.cart[service_id] = 1
        self.save()

    def update(self, service_id, quantity):
        service_id = str(service_id)
        if service_id in self.cart:
            if quantity <= 0:
                self.remove(service_id)
            else:
                self.cart[service_id] = quantity
                self.save()

    def remove(self, service_id):
        service_id = str(service_id)
        if service_id in self.cart:
            del self.cart[service_id]
            self.save()

    def clear(self):
        self.session[CART_SESSION_KEY] = {}
        self.save()

    def save(self):
        self.session.modified = True

    def __len__(self):
        return sum(self.cart.values())

    def __iter__(self):
        services = Service.objects.filter(pk__in=self.cart.keys())
        services_map = {str(s.pk): s for s in services}
        for service_id, quantity in self.cart.items():
            service = services_map.get(service_id)
            if not service:
                continue
            line_total = service.price * quantity
            yield {
                "service": service,
                "quantity": quantity,
                "line_total": line_total,
            }

    def get_items(self):
        return list(self)

    def get_total(self):
        return sum((item["line_total"] for item in self), Decimal("0"))
