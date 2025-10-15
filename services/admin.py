from django.contrib import admin
from .models import Service
from .models import Booking

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('title', 'order')
    list_editable = ('order',)
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ('title',)
    ordering = ('order', 'title')

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('service', 'email', 'booking_date', 'booking_time', 'status')
    list_filter = ('service', 'booking_date', 'status')