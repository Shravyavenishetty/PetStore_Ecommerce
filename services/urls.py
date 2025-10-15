from django.urls import path
from . import views

app_name = 'services'
urlpatterns = [
    path('book/', views.book_service, name='book_service'),
    path('booking-success/', views.booking_success, name='booking_success'),
    path('history/', views.booking_history, name='booking_history'),
    path('payment-success/<int:booking_id>/', views.payment_success, name='payment_success'),
    path('nearby-centers/', views.nearby_service_centers, name='nearby_service_centers'),
    path('<slug:slug>/', views.service_detail, name='service_detail'),
    path('', views.service_list, name='service_list'),
]
