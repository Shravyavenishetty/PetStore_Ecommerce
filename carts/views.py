from django.shortcuts import render, get_object_or_404
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models import F, Sum
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

from .models import Cart, CartItem
from .utils import _cart_id
from shop.models import Pet, Product

CARTABLE_MODELS = {
    "pet": Pet,
    "product": Product,
}

def get_cartable_object(model_name, object_id):
    try:
        model = CARTABLE_MODELS[model_name]
        obj = model.objects.get(pk=object_id)
        return obj, ContentType.objects.get_for_model(obj)
    except (KeyError, model.DoesNotExist):
        return None, None

def get_cart_items_and_totals(request):
    if request.user.is_authenticated:
        cart_items = CartItem.objects.filter(user=request.user, active=True)
    else:
        cart = Cart.objects.filter(cart_id=_cart_id(request)).first()
        cart_items = CartItem.objects.filter(cart=cart, active=True) if cart else []
    total = sum(item.subtotal() for item in cart_items)
    quantity = sum(item.quantity for item in cart_items)
    return cart_items, total, quantity

def remove_from_cart(request, item_id):
    if request.method == "POST":
        cart_item = get_object_or_404(CartItem, id=item_id)
        if cart_item.quantity > 1:
            with transaction.atomic():
                cart_item.quantity = F("quantity") - 1
                cart_item.save()
                cart_item.refresh_from_db()
            remaining = True
        else:
            cart_item.delete()
            remaining = False

        # Find matching cart items & compute totals after removal
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, active=True)
        else:
            cart = Cart.objects.filter(cart_id=_cart_id(request)).first()
            cart_items = CartItem.objects.filter(cart=cart, active=True) if cart else []
        total = sum(item.subtotal() for item in cart_items)
        count = cart_items.aggregate(total=Sum('quantity'))['total'] or 0

        return JsonResponse({
            "success": True,
            "item_id": item_id,
            "quantity": cart_item.quantity if remaining else 0,
            "subtotal": float(cart_item.subtotal()) if remaining else 0,
            "total": float(total),
            "total_qty": count,
            "count": count
        })
    return JsonResponse({"success": False, "error": "POST request required."})

def delete_cart_item(request, item_id):
    if request.method == "POST":
        cart_item = get_object_or_404(CartItem, id=item_id)
        cart_item.delete()
        # Compute new totals after delete
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, active=True)
        else:
            cart = Cart.objects.filter(cart_id=_cart_id(request)).first()
            cart_items = CartItem.objects.filter(cart=cart, active=True) if cart else []
        total = sum(item.subtotal() for item in cart_items)
        count = cart_items.aggregate(total=Sum('quantity'))['total'] or 0
        return JsonResponse({
            "success": True,
            "item_id": item_id,
            "quantity": 0,
            "subtotal": 0,
            "total": float(total),
            "total_qty": count,
            "count": count
        })
    return JsonResponse({"success": False, "error": "POST request required."})

def view_cart(request):
    cart_items, total, quantity = get_cart_items_and_totals(request)
    context = {"cart_items": cart_items, "total": total, "quantity": quantity}
    return render(request, "carts/cart.html", context)

@login_required
def merge_cart(request):
    try:
        session_cart = Cart.objects.get(cart_id=_cart_id(request))
        session_cart_items = CartItem.objects.filter(cart=session_cart)
        user_cart_items = CartItem.objects.filter(user=request.user)
        for s_item in session_cart_items:
            same_item = user_cart_items.filter(
                content_type=s_item.content_type, object_id=s_item.object_id
            ).first()
            if same_item:
                with transaction.atomic():
                    same_item.quantity = F("quantity") + s_item.quantity
                    same_item.save()
                    same_item.refresh_from_db()
                s_item.delete()
            else:
                s_item.user = request.user
                s_item.cart = None
                s_item.save()
        session_cart.delete()
    except Cart.DoesNotExist:
        pass

def cart_count_api(request):
    count = 0
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
    else:
        cart = Cart.objects.filter(cart_id=_cart_id(request)).first()
    if cart:
        count = CartItem.objects.filter(cart=cart, active=True).aggregate(total=Sum('quantity'))['total'] or 0
    return JsonResponse({"count": count})

def add_to_cart(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "POST request required."})

    model = request.POST.get("model")
    object_id = request.POST.get("object_id")
    obj, content_type = get_cartable_object(model, object_id)
    if not obj or not content_type:
        return JsonResponse({"success": False, "error": "Invalid item."})

    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart_item = CartItem.objects.filter(
            user=request.user,
            content_type=content_type,
            object_id=obj.id,
            cart=cart
        ).first()

        if cart_item:
            if not cart_item.active:
                cart_item.active = True
                cart_item.quantity = 1  # or desired default
                cart_item.save()
            else:
                with transaction.atomic():
                    cart_item.quantity = F("quantity") + 1
                    cart_item.save()
                    cart_item.refresh_from_db()
        else:
            cart_item = CartItem.objects.create(
                user=request.user,
                content_type=content_type,
                object_id=obj.id,
                cart=cart,
                quantity=1,
                active=True,
            )
        cart_items = CartItem.objects.filter(cart=cart, active=True)
        count = cart_items.aggregate(total=Sum("quantity"))["total"] or 0
        total = sum(item.subtotal() for item in cart_items)

    else:
        cart, _ = Cart.objects.get_or_create(cart_id=_cart_id(request), user=None)
        cart_item = CartItem.objects.filter(
            cart=cart,
            user=None,
            content_type=content_type,
            object_id=obj.id,
        ).first()

        if cart_item:
            if not cart_item.active:
                cart_item.active = True
                cart_item.quantity = 1
                cart_item.save()
            else:
                with transaction.atomic():
                    cart_item.quantity = F("quantity") + 1
                    cart_item.save()
                    cart_item.refresh_from_db()
        else:
            cart_item = CartItem.objects.create(
                cart=cart,
                user=None,
                content_type=content_type,
                object_id=obj.id,
                quantity=1,
                active=True,
            )
        cart_items = CartItem.objects.filter(cart=cart, active=True)
        count = cart_items.aggregate(total=Sum("quantity"))["total"] or 0
        total = sum(item.subtotal() for item in cart_items)

    return JsonResponse(
        {
            "success": True,
            "count": count,
            "total": float(total),
            "item_id": cart_item.id,
            "quantity": cart_item.quantity,
            "subtotal": float(cart_item.subtotal()),
            "total_qty": count,
        }
    )
