from django.contrib import admin

from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("product_id", "artist", "title", "genre", "product_type", "price")
    list_filter = ("genre", "product_type")
    search_fields = ("product_id", "artist", "title")
