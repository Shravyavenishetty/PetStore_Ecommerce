from .models import WishlistItem

def wishlist_item_count(request):
    count = 0
    if request.user.is_authenticated:
        count = WishlistItem.objects.filter(user=request.user).count()
    return {'wishlist_item_count': count}
