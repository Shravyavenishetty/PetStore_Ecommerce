from django.db import models
from django.conf import settings
from django.db.models import Avg, Count
from django.utils.text import slugify
from django.urls import reverse


class Store(models.Model):
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=50)
    contact_phone = models.CharField(max_length=20)

    def __str__(self):
        return self.name
    

class PetCategory(models.Model):
    name = models.CharField(max_length=50)

    class Meta:
        verbose_name_plural = "Pet Categories"
        db_table = "pet_category"

    def __str__(self):
        return self.name
    
class Pet(models.Model):
    name = models.CharField(max_length=100)
    category = models.ForeignKey(PetCategory,on_delete=models.CASCADE)
    breed = models.CharField(max_length=100,blank=True,null=True,help_text="Variety or breed of the pet")
    age = models.FloatField()
    price = models.DecimalField(max_digits=10,decimal_places=2)
    image = models.ImageField(upload_to='pets/')
    store = models.ForeignKey(Store,on_delete=models.CASCADE,related_name='pets')
    description = models.TextField(blank=True)
    average_rating = models.FloatField(default=0.0)
    review_count = models.PositiveBigIntegerField(default=0)

    def get_absolute_url(self):
        return reverse('shop:pet_detail', args=[self.pk])

    def __str__(self):
        breed_text = f" - {self.breed}" if self.breed else ""
        return f"{self.name}{breed_text} ({self.category})"
    
    def update_rating(self):
        agg = self.reviews.filter(approved=True).aggregate(
            avg = Avg('rating'),
            count = Count('id')
        )
        self.average_rating = agg['avg'] if agg['avg'] else 0.0
        self.review_count = agg['count'] if agg['count'] else 0
        self.save()


class ProductCategory(models.Model):
    name = models.CharField(max_length=50)
    pet_category = models.ForeignKey(PetCategory, on_delete=models.CASCADE)
    slug = models.SlugField(max_length=100, unique=True, blank=True, null=True)
    image = models.ImageField(upload_to='category_images/', blank=True, null=True)

    class Meta:
        verbose_name_plural = "Product Categories"
        db_table = "product_category"

    def __str__(self):
        return f"{self.name} ({self.pet_category.name})"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(f"{self.name} {self.pet_category.name}")
            slug_candidate = base_slug
            num = 1
            while ProductCategory.objects.filter(slug=slug_candidate).exists():
                slug_candidate = f"{base_slug}-{num}"
                num += 1
            self.slug = slug_candidate
        super().save(*args, **kwargs)

    

class Product(models.Model):
    name = models.CharField(max_length=100)
    category = models.ForeignKey(ProductCategory, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to="products/")
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='products')
    description = models.TextField(blank=True)

    def get_absolute_url(self):
        return reverse('shop:product_detail', args=[self.pk])

    def __str__(self):
        return self.name

class PetReview(models.Model):
    pet = models.ForeignKey(Pet, related_name='reviews', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)])  # 1-5 stars
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(default=False)  # For moderation

    def __str__(self):
        return f"{self.user} - {self.pet} ({self.rating} stars)"
    

class Favourite(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='favourites', on_delete=models.CASCADE)
    pet = models.ForeignKey(Pet, related_name='favourited_by', on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'pet')
        ordering = ['-added_at']

    def __str__(self):
        return f"{self.user} favourites {self.pet}"


class Order(models.Model):
    item_name = models.CharField(max_length=200)
    buyer_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    shipping_address = models.TextField()
    payment_method = models.CharField(max_length=50)
    user_upi_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # New fields for tracking
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
    ]
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')

    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"Order #{self.id} for {self.buyer_name}"
