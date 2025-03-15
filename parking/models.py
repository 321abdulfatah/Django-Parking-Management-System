from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission


class User(AbstractUser):
    phone_number = models.CharField(max_length=10, unique=True)
    password = models.CharField(max_length=128)

    groups = models.ManyToManyField(
        Group,
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        related_name="parking_user_groups",  
        related_query_name="user",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name="parking_user_permissions", 
        related_query_name="user",
    )

    def __str__(self):
        return self.username

class Parking(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='parking')
    parking_name = models.CharField(max_length=255, unique=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    price_per_hour = models.DecimalField(max_digits=6, decimal_places=0)
    image = models.ImageField(upload_to='parking_images/')
    is_available = models.BooleanField(default=False)

    def __str__(self):
        return self.parking_name