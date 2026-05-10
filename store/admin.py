from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Product, Order, OrderItem, Review

admin.site.site_header = "Herbal Store Admin"
admin.site.site_title = "Herbal Store Admin"
admin.site.index_title = "Site Administration"

# ================= CATEGORY =================
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)

admin.site.register(Category, CategoryAdmin)


# ================= PRODUCT =================
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category', 'price', 'discount_percent', 'stock', 'image_preview')
    list_filter = ('category',)
    search_fields = ('name', 'description')

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" />', obj.image.url)
        return "No Image"

    image_preview.short_description = "Image"

admin.site.register(Product, ProductAdmin)


# ================= ORDER =================
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'total_amount', 'estimated_delivery', 'created_at')
    list_filter = ('status',)
    search_fields = ('user__username',)
    list_editable = ('status',)

admin.site.register(Order, OrderAdmin)


# ================= ORDER ITEMS =================
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'price')

admin.site.register(OrderItem, OrderItemAdmin)


# ================= REVIEWS =================
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'created_at')

admin.site.register(Review, ReviewAdmin)


# ================= USER PROFILE =================
