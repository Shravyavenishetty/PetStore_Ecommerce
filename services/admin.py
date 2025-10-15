from django.contrib import admin
from .models import Booking,ServiceCenter,Service

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

@admin.register(ServiceCenter)
class ServiceCenterAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'latitude', 'longitude')  # columns to show in list view
    search_fields = ('name', 'address')  # add search box for these fields
    list_filter = ()  # optionally, you can add filters if needed
    ordering = ('name',)  # default ordering by name
