from django.db import models  # <-- Add this import
from .models import CartItem

def cart_item_count(request):
    count = 0
    if request.user.is_authenticated:
        count = CartItem.objects.filter(user=request.user, active=True).aggregate(
            total=models.Sum('quantity')
        )['total'] or 0
    else:
        from .utils import _cart_id
        from .models import Cart
        cart = Cart.objects.filter(cart_id=_cart_id(request)).first()
        if cart:
            count = CartItem.objects.filter(cart=cart, active=True).aggregate(
                total=models.Sum('quantity')
            )['total'] or 0
    return {'cart_item_count': count}
