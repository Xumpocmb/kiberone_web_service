from django.contrib import messages
from django.db.models import Sum, F
from django.shortcuts import render, redirect, get_object_or_404

from app_kiberclub.models import Client
from app_kibershop.models import Category, Product, Cart, Order, OrderItem


def catalog_view(request):
    categories = Category.objects.all()
    context = {
        'categories': categories,
    }
    return render(request, 'app_kibershop/catalog.html', context)



def cart_view(request):
    return render(request, 'app_kibershop/cart_page.html')



def add_to_cart(request, product_id):
    user_id = request.session.get('client_id')
    print(user_id)
    if not user_id:
        print("not user id")
        messages.error(request, 'Вы не авторизованы', extra_tags='danger')
        return redirect(request.META.get('HTTP_REFERER'))

    try:
        product = get_object_or_404(Product, id=product_id)
        print(product.name)
    except Product.DoesNotExist:
        messages.error(request, 'Товар не найден', extra_tags='danger')
        return redirect(request.META.get('HTTP_REFERER'))

    try:
        client = get_object_or_404(Client, crm_id=user_id)
        print(client.name)
        if not client:
            print("not user")
    except Client.DoesNotExist:
        messages.error(request, 'Вы не авторизованы', extra_tags='danger')
        return redirect(request.META.get('HTTP_REFERER'))

    cart_item, created = Cart.objects.get_or_create(
        user=client,
        product=product,
    )

    if not created:
        cart_item.quantity += 1
        cart_item.save()

    return redirect(request.META.get('HTTP_REFERER'))



def remove_from_cart(request, cart_id):
    cart_item = Cart.objects.get(id=cart_id)
    cart_item.delete()
    messages.success(request, 'Товар удален из корзины', extra_tags='success')
    return redirect(request.META.get('HTTP_REFERER'))


def cart_minus(request, cart_id):
    cart_item = Cart.objects.get(id=cart_id)
    if cart_item.quantity == 1:
        return redirect(request.META.get('HTTP_REFERER'))
    cart_item.quantity -= 1
    cart_item.save()
    return redirect(request.META.get('HTTP_REFERER'))

def cart_plus(request, cart_id):
    cart_item = Cart.objects.get(id=cart_id)
    cart_item.quantity += 1
    cart_item.save()
    return redirect(request.META.get('HTTP_REFERER'))


def make_order(request):
    return redirect(request.META.get('HTTP_REFERER'))


def profile_page(request):
    orders = Order.objects.filter(user=Client.objects.get(crm_id=request.session.get('client_id')))
    order_items = OrderItem.objects.filter(order__in=orders)
    total_sum = order_items.aggregate(total_sum=Sum(F('product__price') * F('quantity')))['total_sum'] or 0
    total_quantity = order_items.aggregate(total_quantity=Sum('quantity'))['total_quantity'] or 0

    context = {
        'order_items': order_items,
        'total_sum': total_sum,
        'total_quantity': total_quantity,
    }
    return render(request, 'app_kibershop/profile_page.html', context=context)