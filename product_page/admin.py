from django.contrib import admin

from .models import ProductPage, Review


@admin.register(ProductPage)
class ProductPageAdmin(admin.ModelAdmin):
    list_display = ("product", "release_date")
    search_fields = ("product__product_id", "product__artist", "product__title")


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("product", "author", "rating", "is_approved", "created_at")
    list_filter = ("rating", "is_approved")
    search_fields = ("product__artist", "product__title", "author__username", "comment")
