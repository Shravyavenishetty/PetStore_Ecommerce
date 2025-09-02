from django.urls import path
from . import views

app_name = 'shop'

urlpatterns = [
    path('store/', views.pet_store_home, name='store'),
    path('store/pet/<int:pk>/', views.pet_detail, name='pet_detail'),
    # Toggle favourite for a pet (requires login)
    path('store/pet/<int:pet_id>/toggle-favourite/', views.toggle_favourite, name='toggle_favourite'),
    # Submit a review for a pet (requires login)
    path('store/pet/<int:pet_id>/add-review/', views.add_pet_review, name='add_pet_review'),
    # Optional: Store details page showing pets and products in the store
    path('shop/<int:pk>/', views.store_detail, name='store_detail'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    path('category/<slug:category_slug>/', views.product_list_by_category, name='product_list_by_category'),
    path('categories/', views.product_category_list, name='product_category_list'),
    path('process_order/', views.process_order, name='process_order'), 
    path('buy/<str:model_name>/<int:item_id>/', views.checkout, name='buy_item'),
    path('order-success/', views.order_success, name='order_success'),
    path('checkout/', views.checkout, name='checkout'),
    path('accessories/', views.accessories_all_pets, name='accessories_all_pets'),
    path('medicines/', views.medicines_all_pets, name='medicines_all_pets'),
    path('food/', views.food_all_pets, name='food_all_pets'),
    path('products/', views.all_products, name='all_products'),
    path('bird-cages/', views.bird_cages, name='bird_cages'),
    path('fish-aquarium-supplies/', views.fish_aquarium_supplies, name='fish_aquarium_supplies'),
    path('pet-shops/', views.all_pet_shops, name='all_pet_shops'),
    path('confirm-upi-payment/<int:order_id>/', views.confirm_upi_payment, name='confirm_upi_payment'),
]
