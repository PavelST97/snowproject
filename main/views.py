from django.db import transaction
from django.shortcuts import render
from django.views.generic import DetailView, ListView, View
from django.http import HttpResponseRedirect
from django.contrib import messages

from .models import Product, Category, Customer, Cart, CartProduct
from .mixins import CartMixin, ProductListViewMixin
from .forms import OrderForm
from .utils import recalc_cart


class BaseView(CartMixin, View):

    def get(self, request, *args, **kwargs):
        products = Product.objects.all().order_by('-id')[:4]
        # categories = Category.objects.all()
        categories = Category.objects.get_categories_for_navbar()
        context = {
            'products': products,
            'cart': self.cart,
            'categories': categories
        }
        return render(request, 'main/base.html', context)


class ProductDetailView(CartMixin, ProductListViewMixin, DetailView):

    model = Product
    queryset = Product.objects.all()
    context_object_name = 'product'
    template_name = 'main/product_detail.html'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cart'] = self.cart
        return context


class ProductListView(CartMixin, ProductListViewMixin, DetailView):

    model = Category
    queryset = Category.objects.all()
    context_object_name = 'product_list'
    slug_url_kwarg = 'slug'
    template_name = 'main/product_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cart'] = self.cart
        return context


class ChangeQTYView(CartMixin, View):

    def post(self, request, *args, **kwargs):
        product_slug = kwargs.get('slug')
        product = Product.objects.get(slug=product_slug)
        cart_product = CartProduct.objects.get(
            user=self.cart.owner, cart=self.cart, product=product
        )
        qty = int(request.POST.get('qty'))
        cart_product.qty = qty
        cart_product.save()
        recalc_cart(self.cart)
        messages.add_message(request, messages.INFO, 'Кол-во успешно изменено!')
        return HttpResponseRedirect('/cart/')


class CartView(CartMixin, View):

    def get(self, request, *args, **kwargs):
        categories = Category.objects.get_categories_for_navbar()
        context = {
            'cart': self.cart,
            'categories': categories
        }
        return render(request, 'main/cart.html', context)


class AddToCartView(CartMixin, View):

    def get(self, request, *args, **kwargs):
        product_slug = kwargs.get('slug')
        product = Product.objects.get(slug=product_slug)
        cart_product, created = CartProduct.objects.get_or_create(
            user=self.cart.owner, cart=self.cart, product=product
        )
        if created:
            self.cart.products.add(cart_product)
        recalc_cart(self.cart)
        messages.add_message(request, messages.INFO, 'Товар успешно добавлен!')
        return HttpResponseRedirect('/cart/')


class DeleteFromCartView(CartMixin, View):

    def get(self, request, *args, **kwargs):
        product_slug = kwargs.get('slug')
        product = Product.objects.get(slug=product_slug)
        cart_product = CartProduct.objects.get(
            user=self.cart.owner, cart=self.cart, product=product
        )
        self.cart.products.remove(cart_product)
        cart_product.delete()
        recalc_cart(self.cart)
        messages.add_message(request, messages.INFO, 'Товар успешно удален!')
        return HttpResponseRedirect('/cart/')


class CheckoutView(CartMixin, View):

    def get(self, request, *args, **kwargs):
        categories = Category.objects.get_categories_for_navbar()
        form = OrderForm(request.POST or None)
        context = {
            'cart': self.cart,
            'categories': categories,
            'form': form
        }
        return render(request, 'main/checkout.html', context)


class MakeOrderView(CartMixin, View):

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        form = OrderForm(request.POST or None)
        customer = Customer.objects.get(user=request.user)
        if form.is_valid():
            new_order = form.save(commit=False)
            new_order.customer = customer
            new_order.first_name = form.cleaned_data['first_name']
            new_order.last_name = form.cleaned_data['last_name']
            new_order.phone = form.cleaned_data['phone']
            new_order.address = form.cleaned_data['address']
            new_order.buying_type = form.cleaned_data['buying_type']
            new_order.order_date = form.cleaned_data['order_date']
            new_order.comment = form.cleaned_data['comment']
            new_order.save()
            self.cart.in_order = True
            self.cart.save()
            new_order.cart = self.cart
            new_order.save()
            messages.add_message(request, messages.INFO, 'Спасибо за заказ! Менеджер с Вами свяжется')
            customer.order.add(new_order)
            return HttpResponseRedirect('/')
        return HttpResponseRedirect('/checkout/')
