from django.urls import path
from . import views

app_name = 'wishlist'

urlpatterns = [
    path('', views.view_wishlist, name='view'),
    path('toggle/', views.toggle_wishlist, name='toggle_wishlist'),
    path('count/', views.wishlist_count_api, name='wishlist_count_api'),
]
