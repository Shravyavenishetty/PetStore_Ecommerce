from django.contrib import admin

from .models import Pet, PetCategory, Store, ProductCategory, Product, PetReview, Favourite,Order

admin.site.register(Pet)
admin.site.register(PetCategory)
admin.site.register(Store)
admin.site.register(ProductCategory)
admin.site.register(Product)
admin.site.register(PetReview)
admin.site.register(Favourite)
admin.site.register(Order)