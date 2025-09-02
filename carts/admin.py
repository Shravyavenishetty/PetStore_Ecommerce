from django.contrib import admin
from .models import Cart, CartItem


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("cart_id", "date_added", "user")
    search_fields = ("cart_id", "user__username")


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ("item_name", "cart", "user", "quantity", "active")
    list_filter = ("active", "cart")
    search_fields = ("user__username",)

    readonly_fields = ("content_object",)

    def item_name(self, obj):
        """
        Display the name of the related object (pet, product, etc.)
        """
        try:
            return obj.content_object.name
        except AttributeError:
            return str(obj.content_object)
