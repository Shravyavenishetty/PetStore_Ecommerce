from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class Cart(models.Model):
    cart_id = models.CharField(max_length=250, unique=True)
    date_added = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True
    )

    def __str__(self):
        return self.cart_id

    def total_price(self):
        return sum(item.subtotal() for item in self.items.filter(active=True))

    def total_quantity(self):
        return sum(item.quantity for item in self.items.filter(active=True))


class CartItem(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True
    )
    cart = models.ForeignKey(
        Cart, on_delete=models.CASCADE, null=True, blank=True, related_name="items"
    )
    quantity = models.PositiveIntegerField(default=1)
    active = models.BooleanField(default=True)

    # Generic relations: support any cartable model, e.g. Pet, Product, etc.
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE,null=True,blank=True)
    object_id = models.PositiveIntegerField(null=True,blank=True)
    content_object = GenericForeignKey("content_type", "object_id")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "content_type", "object_id"],
                condition=models.Q(user__isnull=False),
                name="unique_user_item"
            ),
            models.UniqueConstraint(
                fields=["cart", "content_type", "object_id"],
                condition=models.Q(cart__isnull=False),
                name="unique_cart_item"
            ),
        ]

    def subtotal(self):
        return getattr(self.content_object, "price", 0) * self.quantity

    def __str__(self):
        try:
            name = getattr(self.content_object, "name", str(self.object_id))
            return f"{name} ({self.quantity})"
        except Exception:
            return f"CartItem ({self.quantity})"

    def item_name(self):
        try:
            return getattr(self.content_object, "name", str(self.object_id))
        except Exception:
            return str(self.object_id)
    item_name.short_description = "Item"
