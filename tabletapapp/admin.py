from django.contrib import admin
from .models import User, Restaurant, Menu, Category, MenuItem, OrderItem, Order
# Register your models here.
admin.site.register(User)
admin.site.register(Restaurant)
admin.site.register(Menu)
admin.site.register(Category)
admin.site.register(MenuItem)
admin.site.register(OrderItem)
admin.site.register(Order)
