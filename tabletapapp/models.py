from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid

# --- Custom User Model ---
class User(AbstractUser):
    restaurant = models.ForeignKey('Restaurant', on_delete=models.SET_NULL, null=True, blank=True)

# --- Restaurant Model ---
class Restaurant(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=15)
    address = models.TextField()
    number_of_tables = models.PositiveIntegerField()

    def __str__(self):
        return self.name

# --- Menu, Category, Item ---
class Menu(models.Model):
    name = models.CharField(max_length=100)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)

class Category(models.Model):
    name = models.CharField(max_length=100)
    menu = models.ForeignKey(Menu, on_delete=models.CASCADE)

class MenuItem(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='media/', null=True, blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)

# --- Order ---
class Order(models.Model):
    STATUS_CHOICES = (
        ('received', 'Received'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
    )
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
    table_number = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='received')
    created_at = models.DateTimeField(auto_now_add=True)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
