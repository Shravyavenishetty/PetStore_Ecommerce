from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib.contenttypes.models import ContentType

from .models import WishlistItem


@login_required
def view_wishlist(request):
    items = WishlistItem.objects.filter(user=request.user).select_related('content_type')
    context = {'wishlist_items': items}
    return render(request, 'wishlist/wishlist.html', context)


@login_required
def toggle_wishlist(request):
    if request.method == 'POST':
        model = request.POST.get('model')
        object_id = request.POST.get('object_id')

        if not model or not object_id:
            return JsonResponse({'success': False, 'error': 'Missing model or object ID.'}, status=400)

        try:
            content_type = ContentType.objects.get(model=model.lower())
            model_class = content_type.model_class()
            obj = model_class.objects.get(pk=object_id)
        except ContentType.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Invalid model type.'}, status=400)
        except model_class.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Item does not exist.'}, status=404)

        user = request.user
        wishlist_qs = WishlistItem.objects.filter(user=user, content_type=content_type, object_id=object_id)

        if wishlist_qs.exists():
            wishlist_qs.delete()
            count = WishlistItem.objects.filter(user=user).count()
            return JsonResponse({'success': True, 'added': False, 'count': count})
        else:
            WishlistItem.objects.create(user=user, content_type=content_type, object_id=object_id)
            count = WishlistItem.objects.filter(user=user).count()
            return JsonResponse({'success': True, 'added': True, 'count': count})

    return JsonResponse({'success': False, 'error': 'Invalid HTTP method.'}, status=405)

def wishlist_count_api(request):
    if request.user.is_authenticated:
        count = WishlistItem.objects.filter(user=request.user).count()
    else:
        count = 0
    return JsonResponse({"count": count})

