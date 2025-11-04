from decimal import Decimal
from django.db import models


class Table(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return f"Mesa {self.name}"


class ProductCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=255)
    category = models.ForeignKey(ProductCategory, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    UNITS = [
        ("oz", "Onzas"),
        ("lb", "Libras"),
        ("g", "Gramos"),
        ("kg", "Kilogramos"),
        ("ml", "Mililitros"),
        ("l", "Litros"),
        ("und", "Unidades"),
    ]

    name = models.CharField(max_length=255, unique=True, verbose_name="Nombre")
    stock_quantity = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name="Cantidad"
    )
    unit = models.CharField(
        max_length=10, choices=UNITS, default="und", verbose_name="Unidad"
    )

    def add_stock(self, amount):
        """Agrega cantidad al stock."""
        self.stock_quantity += Decimal(amount)
        self.save()

    def __str__(self):
        return f"{self.name} ({self.stock_quantity} {self.unit})"


class ProductIngredient(models.Model):
    """Relación de ingredientes que usa cada producto."""

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} {self.ingredient.unit} de {self.ingredient.name} para {self.product.name}"


class IngredientMovement(models.Model):
    """Registra todo movimiento de inventario (uso, compra, ajuste, etc.)"""

    ingredient = models.ForeignKey("Ingredient", on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.CharField(max_length=255, blank=True, null=True)
    user = models.ForeignKey("auth.User", on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def apply_movement(self):
        """Aplica el movimiento al inventario."""
        self.ingredient.add_stock(self.quantity)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            self.apply_movement()

    def __str__(self):
        tipo = "Ingreso" if self.quantity >= 0 else "Salida"
        return f"{tipo}: {self.quantity} {self.ingredient.unit} de {self.ingredient.name}"


class Order(models.Model):
    table = models.ForeignKey(Table, on_delete=models.SET_NULL, null=True, blank=True)
    user = models.ForeignKey("auth.User", on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_paid = models.BooleanField(default=False)
    
    def get_status_display(self):
        return "Pagada" if self.is_paid else "Pendiente"

    def get_total(self):
        return sum(item.get_total() for item in self.orderitem_set.all())

    def __str__(self):
        return f"Orden {self.id} - {self.table.name if self.table else 'Sin mesa'}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def get_total(self):
        return self.quantity * self.product.price

    def save(self, *args, **kwargs):
        """Guarda el pedido y actualiza el inventario de ingredientes."""
        super().save(*args, **kwargs)

        for prod_ing in ProductIngredient.objects.filter(product=self.product):
            total_required = prod_ing.quantity * Decimal(self.quantity)

            IngredientMovement.objects.create(
                ingredient=prod_ing.ingredient,
                quantity=-total_required,
                user=self.order.user,
                reason=f"Uso en {self.product.name}, Comanda #{self.order.id}",
            )


    def __str__(self):
        return f"{self.quantity} x {self.product.name} (Comanda #{self.order.id})"
