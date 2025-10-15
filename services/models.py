from django.db import models
from django.utils.text import slugify
from django.conf import settings

class Service(models.Model):
    title = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField()
    icon_class = models.CharField(max_length=50, default='fas fa-paw', help_text="Font Awesome icon class, e.g. 'fas fa-dog'")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'title']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

class Booking(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookings', null=True, blank=True)
    email = models.EmailField(max_length=254,blank=True, null=True, help_text="If not logged in, please provide your email.")
    service = models.ForeignKey(Service, on_delete=models.CASCADE,related_name='bookings')
    pet_name = models.CharField(max_length=100)
    pet_type = models.CharField(max_length=100)
    booking_date = models.DateField()
    booking_time = models.TimeField()
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    is_paid = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.service.title} - {self.email or self.user} on {self.booking_date} at {self.booking_time}"