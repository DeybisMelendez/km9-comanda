from django.contrib import admin
from .models import (
    Table,
    ProductCategory,
    Product,
    Ingredient,
    ProductIngredient,
    IngredientUsage,
    IngredientStockAdjustment,
    Order,
    OrderItem,
)


@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


class ProductIngredientInline(admin.TabularInline):
    model = ProductIngredient
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price")
    search_fields = ("name",)
    list_filter = ("category",)
    inlines = [ProductIngredientInline]


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ("name", "stock_quantity", "unit")
    list_filter = ("unit",)
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(ProductIngredient)
class ProductIngredientAdmin(admin.ModelAdmin):
    list_display = ("product", "ingredient", "quantity")
    list_filter = ("product", "ingredient")
    search_fields = ("product__name", "ingredient__name")


@admin.register(IngredientUsage)
class IngredientUsageAdmin(admin.ModelAdmin):
    list_display = ("ingredient", "quantity_used", "unit", "order_item", "created_at")
    list_filter = ("ingredient", "unit", "created_at")
    search_fields = ("ingredient__name", "order_item__product__name")
    date_hierarchy = "created_at"


@admin.register(IngredientStockAdjustment)
class IngredientStockAdjustmentAdmin(admin.ModelAdmin):
    list_display = ("ingredient", "quantity", "reason", "adjusted_at")
    list_filter = ("ingredient", "adjusted_at")
    search_fields = ("ingredient__name", "reason")
    date_hierarchy = "adjusted_at"


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "table", "status", "created_at", "get_total_display")
    list_filter = ("status", "created_at", "table")
    date_hierarchy = "created_at"
    inlines = [OrderItemInline]

    def get_total_display(self, obj):
        return f"C${obj.get_total():,.2f}"
    get_total_display.short_description = "Total"


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "product", "quantity", "get_total_display")
    list_filter = ("order__status", "product")
    search_fields = ("product__name", "order__id")

    def get_total_display(self, obj):
        return f"C${obj.get_total():,.2f}"
    get_total_display.short_description = "Subtotal"
