from django.contrib import admin
from .models import (
    Table,
    ProductCategory,
    DispatchArea,
    Product,
    Ingredient,
    ProductIngredient,
    IngredientMovement,
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

@admin.register(DispatchArea)
class DispatchAreaAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


class ProductIngredientInline(admin.TabularInline):
    model = ProductIngredient
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "dispatch_area", "price")
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

@admin.register(IngredientMovement)
class IngredientMovementAdmin(admin.ModelAdmin):
    list_display = ("ingredient", "quantity", "reason", "user", "created_at")
    list_filter = ("ingredient", "user", "created_at")
    search_fields = ("ingredient__name", "reason", "user__username")
    ordering = ("-created_at",)
    readonly_fields = ("created_at",)

    def save_model(self, request, obj, form, change):
        """Asigna automáticamente el usuario que realiza el movimiento."""
        if not obj.user:
            obj.user = request.user
        super().save_model(request, obj, form, change)

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "table", "is_paid", "created_at", "get_total_display")
    list_filter = ("is_paid", "created_at", "table")
    date_hierarchy = "created_at"
    inlines = [OrderItemInline]

    def get_total_display(self, obj):
        return f"C${obj.get_total():,.2f}"
    get_total_display.short_description = "Total"


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "product", "quantity", "get_total_display")
    list_filter = ("order__is_paid", "product")
    search_fields = ("product__name", "order__id")

    def get_total_display(self, obj):
        return f"C${obj.get_total():,.2f}"
    get_total_display.short_description = "Subtotal"
