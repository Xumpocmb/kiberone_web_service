from app_api.alfa_crm_service.crm_service import get_client_kiberons
from app_kiberclub.models import Client
from app_kibershop.models import Cart, Order


def cart(request):
    if not request.session.get('client_id'):
        return {'carts': []}

    client = Client.objects.filter(crm_id=request.session.get('client_id')).first()

    if not client:
        return {'carts': []}
    try:
        carts = Cart.objects.filter(user=Client.objects.get(crm_id=request.session.get('client_id')))
    except Cart.DoesNotExist:
        return {'carts': []}

    return {'carts': carts if carts.exists() else []}


def get_user_kiberons(request):
    client_id = request.session.get('client_id')
    if not client_id:
        return {'kiberons': 0}

    client = Client.objects.filter(crm_id=client_id).first()
    if not client:
        return {'kiberons': 0}

    try:
        user_kiberons_count = get_client_kiberons(client.branch.id, client_id)
    except Exception as e:
        return {'kiberons': "0"}

    return {"kiberons": user_kiberons_count}
