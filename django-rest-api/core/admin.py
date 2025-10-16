from django.contrib import admin

from .models import NutritionHistory, Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('product_name', 'brand', 'category', 'nutri_score')
    search_fields = ('product_name', 'brand')
    list_filter = ('category', 'nutri_score')

@admin.register(NutritionHistory)
class NutritionHistoryAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'scan_date', 'nutri_score')
    list_filter = ('nutri_score', 'scan_date')
    search_fields = ('product__product_name', 'user__username') 