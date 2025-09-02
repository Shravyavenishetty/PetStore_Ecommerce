from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline, GenericStackedInline
from .models import WishlistItem

class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ('user', 'content_object', 'added_at')
    list_filter = ('user', 'content_type')
    search_fields = ('user__username',)

    # Optional: to make content_object clickable and richer display in admin
    readonly_fields = ('content_object',)

admin.site.register(WishlistItem, WishlistItemAdmin)
