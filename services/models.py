from django.db import models
from django.utils.text import slugify

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
