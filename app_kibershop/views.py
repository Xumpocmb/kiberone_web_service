from django.shortcuts import render

from app_kibershop.models import Category


def catalog_view(request):
    categories = Category.objects.all()
    context = {
        'categories': categories,
    }
    return render(request, 'app_kibershop/catalog.html', context)



def cart_view(request):
    return render(request, 'app_kibershop/cart_page.html')



def add_to_cart(request, product_id):
    pass



def remove_from_cart(request, cart_id):
    pass


def cart_minus(request, cart_id):
    pass

def cart_plus(request, cart_id):
    pass


def make_order(request):
    pass


def profile_page(request):
    pass