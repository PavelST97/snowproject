from django.db import models
import requests

APPID = "bb1a9b37ade000a570acf992eb1c7985"


def current_weather(q: str, appid: str = APPID, units='metric') -> dict:
    URL_BASE = "http://api.openweathermap.org/data/2.5/"
    return requests.get(URL_BASE + "weather", params=locals()).json()


def recalc_cart(cart):
    cart_data = cart.products.aggregate(models.Sum('final_price'), models.Count('id'))
    if cart_data.get('final_price__sum'):
        cart.final_price = cart_data['final_price__sum']
    else:
        cart.final_price = 0
    print(cart.products.all())
    total_products = 0
    for products in cart.products.all():
        total_products += products.qty
    cart.total_products = total_products
    cart.save()
