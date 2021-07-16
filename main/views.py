from django.db import transaction
from django.shortcuts import render
from django.views.generic import DetailView, View
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.contrib.auth import authenticate, login

from .models import Product, Category, Customer, Order, CartProduct
from .mixins import CartMixin, ProductListViewMixin
from .forms import OrderForm, LoginForm, RegistrationForm
from .utils import recalc_cart, current_weather


class BaseView(CartMixin, View):

    def get(self, request, *args, **kwargs):
        weather_lahoysk = int(current_weather('логойск')['main']['temp'])
        weather_silichi = int(current_weather('силичи')['main']['temp'])
        products = Product.objects.filter(discount=False).order_by('-id')[:4]
        product_discount = Product.objects.filter(discount=True).order_by('-id')[:3]
        categories = Category.objects.get_categories_for_navbar()
        context = {
            'products': products,
            'cart': self.cart,
            'categories': categories,
            'product_discount': product_discount,
            'weather_lahoysk': weather_lahoysk,
            'weather_silichi': weather_silichi
        }
        return render(request, 'main/base.html', context)


class AboutView(CartMixin, View):

    def get(self, request, *args, **kwargs):
        weather_lahoysk = int(current_weather('логойск')['main']['temp'])
        weather_silichi = int(current_weather('силичи')['main']['temp'])
        categories = Category.objects.get_categories_for_navbar()
        context = {
            'cart': self.cart,
            'categories': categories,
            'weather_lahoysk': weather_lahoysk,
            'weather_silichi': weather_silichi
        }
        return render(request, 'main/about.html', context)


class ContactsView(CartMixin, View):

    def get(self, request, *args, **kwargs):
        weather_lahoysk = int(current_weather('логойск')['main']['temp'])
        weather_silichi = int(current_weather('силичи')['main']['temp'])
        categories = Category.objects.get_categories_for_navbar()
        context = {
            'cart': self.cart,
            'categories': categories,
            'weather_lahoysk': weather_lahoysk,
            'weather_silichi': weather_silichi
        }
        return render(request, 'main/contacts.html', context)


class ProductDetailView(CartMixin, ProductListViewMixin, DetailView):
    model = Product
    queryset = Product.objects.all()
    context_object_name = 'product'
    template_name = 'main/product_detail.html'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cart'] = self.cart
        context['weather_lahoysk'] = int(current_weather('логойск')['main']['temp'])
        context['weather_silichi'] = int(current_weather('силичи')['main']['temp'])
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
        context['weather_lahoysk'] = int(current_weather('логойск')['main']['temp'])
        context['weather_silichi'] = int(current_weather('силичи')['main']['temp'])
        return context


class ProductDiscount(CartMixin, View):

    def get(self, request, *args, **kwargs):

        product_discount = Product.objects.filter(discount=True)
        categories = Category.objects.get_categories_for_navbar()
        weather_lahoysk = int(current_weather('логойск')['main']['temp'])
        weather_silichi = int(current_weather('силичи')['main']['temp'])
        context = {
            'cart': self.cart,
            'product_discount': product_discount,
            'categories': categories,
            'weather_lahoysk': weather_lahoysk,
            'weather_silichi': weather_silichi
        }
        return render(request, 'main/discount.html', context)


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
        weather_lahoysk = int(current_weather('логойск')['main']['temp'])
        weather_silichi = int(current_weather('силичи')['main']['temp'])
        context = {
            'cart': self.cart,
            'categories': categories,
            'weather_lahoysk': weather_lahoysk,
            'weather_silichi': weather_silichi
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
        return HttpResponseRedirect('/')


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
        weather_lahoysk = int(current_weather('логойск')['main']['temp'])
        weather_silichi = int(current_weather('силичи')['main']['temp'])
        form = OrderForm(request.POST or None)
        context = {
            'cart': self.cart,
            'categories': categories,
            'form': form,
            'weather_lahoysk': weather_lahoysk,
            'weather_silichi': weather_silichi
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


class LoginView(CartMixin, View):

    def get(self, request, *args, **kwargs):
        weather_lahoysk = int(current_weather('логойск')['main']['temp'])
        weather_silichi = int(current_weather('силичи')['main']['temp'])
        form = LoginForm(request.POST or None)
        context = {
            'form': form,
            'cart': self.cart,
            'weather_lahoysk': weather_lahoysk,
            'weather_silichi': weather_silichi
        }
        return render(request, 'main/login.html', context)

    def post(self, request, *args, **kwargs):
        form = LoginForm(request.POST or None)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)
            if user:
                login(request, user)
                return HttpResponseRedirect('/')
        context = {'form': form, 'cart': self.cart}
        return render(request, 'main/login.html', context)


class RegistrationView(CartMixin, View):

    def get(self, request, *args, **kwargs):
        weather_lahoysk = int(current_weather('логойск')['main']['temp'])
        weather_silichi = int(current_weather('силичи')['main']['temp'])
        form = RegistrationForm(request.POST or None)
        context = {
            'form': form,
            'cart': self.cart,
            'weather_lahoysk': weather_lahoysk,
            'weather_silichi': weather_silichi
        }
        return render(request, 'main/registration.html', context)

    def post(self, request, *args, **kwargs):
        form = RegistrationForm(request.POST or None)
        if form.is_valid():
            new_user = form.save(commit=False)
            new_user.username = form.cleaned_data['username']
            new_user.email = form.cleaned_data['email']
            new_user.first_name = form.cleaned_data['first_name']
            new_user.last_name = form.cleaned_data['last_name']
            new_user.save()
            new_user.set_password(form.cleaned_data['password'])
            new_user.save()
            Customer.objects.create(
                user=new_user,
                phone=form.cleaned_data['phone'],
                address=form.cleaned_data['address']
            )
            user = authenticate(username=form.cleaned_data['username'], password=form.cleaned_data['password'])
            if user:
                login(request, user)
                return HttpResponseRedirect('/')
        context = {'form': form, 'cart': self.cart}
        return render(request, 'main/login.html', context)


class ProfileView(CartMixin, View):

    def get(self, request, *args, **kwargs):
        customer = Customer.objects.get(user=request.user)
        orders = Order.objects.filter(customer=customer).order_by('-created_at')
        categories = Category.objects.get_categories_for_navbar()
        weather_lahoysk = int(current_weather('логойск')['main']['temp'])
        weather_silichi = int(current_weather('силичи')['main']['temp'])
        context = {
            'cart': self.cart,
            'orders': orders,
            'categories': categories,
            'weather_lahoysk': weather_lahoysk,
            'weather_silichi': weather_silichi
        }
        return render(request, 'main/profile.html', context)
