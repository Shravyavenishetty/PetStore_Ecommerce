from django.urls import path
from . import views

app_name = "carts"

urlpatterns = [
    path("", views.view_cart, name="view"),
    path("add/", views.add_to_cart, name="add_to_cart"),  # POST with model & object_id
    path("remove/<int:item_id>/", views.remove_from_cart, name="remove_from_cart"),
    path("delete/<int:item_id>/", views.delete_cart_item, name="delete_cart_item"),
    path('count/', views.cart_count_api, name='cart_count_api'),

]
