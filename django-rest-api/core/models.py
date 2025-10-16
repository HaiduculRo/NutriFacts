import uuid

from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone


def get_current_datetime():
    return timezone.now().strftime('%Y-%m-%d %H:%M:%S')

def user_profile_picture_path(instance, filename):
    # Pozele vor fi salvate în media/profile_pictures/user_id/filename
    return f'profile_pictures/{instance.user.id}/{filename}'

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    profile_picture = models.ImageField(upload_to=user_profile_picture_path, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s profile"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product_name = models.CharField(max_length=255)
    brand = models.CharField(max_length=255)
    category = models.CharField(max_length=100)
    nutri_score = models.CharField(max_length=1, choices=[
        ('A', 'A'),
        ('B', 'B'),
        ('C', 'C'),
        ('D', 'D'),
        ('E', 'E'),
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.brand} - {self.product_name}"

    class Meta:
        ordering = ['-created_at']

class NutritionHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='nutrition_history')
    fat_100g = models.DecimalField(max_digits=5, decimal_places=2)
    saturated_fat_100g = models.DecimalField(max_digits=5, decimal_places=2)
    trans_fat_100g = models.DecimalField(max_digits=5, decimal_places=2)
    cholesterol_100g = models.DecimalField(max_digits=5, decimal_places=2)
    sodium_100g = models.DecimalField(max_digits=5, decimal_places=2)
    carbohydrates_100g = models.DecimalField(max_digits=5, decimal_places=2)
    fiber_100g = models.DecimalField(max_digits=5, decimal_places=2)
    sugars_100g = models.DecimalField(max_digits=5, decimal_places=2)
    proteins_100g = models.DecimalField(max_digits=5, decimal_places=2)
    nutri_score = models.CharField(max_length=1, choices=[
        ('A', 'A'),
        ('B', 'B'),
        ('C', 'C'),
        ('D', 'D'),
        ('E', 'E'),
    ])
    portion_size = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    image_url = models.URLField(max_length=500, null=True, blank=True)
    scan_date = models.CharField(max_length=50, default=get_current_datetime)

    def __str__(self):
        return f"{self.product.product_name} - {self.scan_date}"

    class Meta:
        ordering = ['-scan_date']
        verbose_name_plural = 'Nutrition History' 