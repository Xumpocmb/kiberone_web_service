from app_kiberclub.models import Client
from app_kibershop.models import Cart, Order, ClientKiberons


def cart(request):
    if not request.session.get('client_id'):
        return {'carts': []}
    carts = Cart.objects.filter(user=Client.objects.get(crm_id=request.session.get('client_id')))

    return {'carts': carts if carts.exists() else []}


def get_user_kiberons(request):
    if request.session.get('client_id'):
        client_id = request.session.get('client_id')
        client = Client.objects.filter(crm_id=client_id).first()
        user_orders = Order.objects.filter(user=Client.objects.get(crm_id=request.session.get('client_id')))
        try:
            user_kiberons = ClientKiberons.objects.get(client=client)
        except ClientKiberons.DoesNotExist:
            return {'kiberons': "0"}

        if user_orders.exists():
            if user_kiberons:
                return {'kiberons': user_kiberons.remain_kiberons_count}
        else:
            return {'kiberons': user_kiberons.start_kiberons_count}
    else:
        return {'kiberons': 0}

