
from django.contrib import admin
from .models import Product

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'new_price', 'stock', 'is_new_arrival')
    list_filter = ('is_new_arrival',)
    search_fields = ('name', 'short_description')
