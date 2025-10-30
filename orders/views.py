from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.utils import timezone
from django.contrib.auth.models import User
from django.db import transaction
from decimal import Decimal
import csv
from .models import (
    Table, Product, Order, OrderItem,
    Ingredient, IngredientStockAdjustment
)


# -------------------------
# 1. Selección de Mesa
# -------------------------
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, F
from .models import Table, Order, OrderItem


@login_required
def table_list(request):
    tables = Table.objects.all().order_by("name")
    table_data = []
    for table in tables:
        # Total de órdenes pendientes o servidas
        total_due = (
            Order.objects.filter(table=table, is_paid=False)
            .annotate(order_total=Sum(F("orderitem__quantity") * F("orderitem__product__price")))
            .aggregate(total=Sum("order_total"))["total"]
            or 0
        )
        table_data.append({"table": table, "total_due": total_due})

    return render(request, "table_list.html", {"table_data": table_data})


@login_required
def table_orders(request, table_id):
    table = get_object_or_404(Table, id=table_id)
    orders = (
        Order.objects.filter(table=table, is_paid=False)
        .prefetch_related("orderitem_set__product")
        .order_by("-created_at")
    )

    return render(request, "table_orders.html", {"table": table, "orders": orders})


@login_required
def mark_table_paid(request, table_id):
    """Marca todas las órdenes pendientes o servidas de la mesa como pagadas."""
    table = get_object_or_404(Table, id=table_id)
    orders = Order.objects.filter(table=table, is_paid=False)
    for order in orders:
        order.is_paid = True
        order.save()
    messages.success(request, f"Comandas de la mesa {table.name} marcada como pagada.")
    return redirect("table_list")


# -------------------------
# 2. Crear Comanda
# -------------------------
@login_required
def create_order(request, table_id):
    table = get_object_or_404(Table, id=table_id)
    products = Product.objects.all().order_by("category__name", "name")

    if request.method == "POST":
        order = Order.objects.create(table=table)
        for key, value in request.POST.items():
            if key.startswith("product_") and int(value) > 0:
                product_id = key.split("_")[1]
                product = Product.objects.get(id=product_id)
                OrderItem.objects.create(order=order, product=product, quantity=int(value))
        messages.success(request, "Comanda creada con éxito.")
        return redirect("order_detail", order.id)

    return render(request, "create_order.html", {
        "table": table,
        "products": products,
    })


# -------------------------
# 3. Detalle / Modificar Comanda
# -------------------------
@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    items = order.orderitem_set.all()

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "mark_paid":
            order.is_paid = True
            order.save()
            messages.success(request, f"Comanda #{order.id} marcada como pagada.")
            return redirect("table_list")

    return render(request, "order_detail.html", {
        "order": order,
        "items": items,
        "total": order.get_total(),
    })

@login_required
def edit_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    tables = Table.objects.all().order_by("name")
    users = User.objects.all().order_by("username")

    if request.method == "POST":
        table_id = request.POST.get("table")
        user_id = request.POST.get("user")
        is_paid = request.POST.get("is_paid") == "on"

        order.table = Table.objects.get(id=table_id) if table_id else None
        order.user = User.objects.get(id=user_id) if user_id else None
        order.is_paid = is_paid
        order.save()

        messages.success(request, "✅ Comanda actualizada correctamente.")
        return redirect("order_detail", order_id=order.id)

    return render(
        request,
        "edit_order.html",
        {"order": order, "tables": tables, "users": users},
    )


# -------------------------
# 4. Historial de Comandas
# -------------------------
@login_required
def order_history(request):
    today = timezone.now().date()
    orders = Order.objects.filter(created_at__date=today).order_by("-created_at")
    return render(request, "order_history.html", {"orders": orders, "today": today})


# -------------------------
# 5. Reporte de Ventas del Día
# -------------------------
@login_required
def daily_report(request):
    today = timezone.now().date()
    orders = Order.objects.filter(created_at__date=today, is_paid="True").order_by("-created_at")

    total_sales = sum(o.get_total() for o in orders)
    product_summary = {}
    for order in orders:
        for item in order.orderitem_set.all():
            product_summary[item.product.name] = product_summary.get(item.product.name, 0) + item.quantity

    return render(request, "daily_report.html", {
        "orders": orders,
        "today": today,
        "total_sales": total_sales,
        "product_summary": product_summary,
    })


# -------------------------
# 6. Ajustes / Compras de Inventario
# -------------------------
@login_required
def inventory_adjustment(request):
    ingredients = Ingredient.objects.all().order_by("name")

    if request.method == "POST":
        # Usamos una transacción para asegurar consistencia
        with transaction.atomic():
            for ingredient in ingredients:
                field_name = f"found_{ingredient.id}"
                found_qty_str = request.POST.get(field_name)
                if found_qty_str is None or found_qty_str.strip() == "":
                    continue

                found_qty = Decimal(found_qty_str)
                diff = found_qty - ingredient.stock_quantity

                # Si hay diferencia, generamos ajuste
                if diff != 0:
                    IngredientStockAdjustment.objects.create(
                        ingredient=ingredient,
                        quantity=diff,
                        reason=f"Ajuste por inventario físico (hecho por {request.user.username})",
                    )

            messages.success(request, "✅ Ajustes de inventario aplicados correctamente.")
        return redirect("inventory")

    return render(request, "inventory.html", {"ingredients": ingredients})

@login_required
def purchase_ingredients(request):
    ingredients = Ingredient.objects.all().order_by("name")

    if request.method == "POST":
        with transaction.atomic():
            count = 0
            for ingredient in ingredients:
                field_name = f"purchase_{ingredient.id}"
                qty_str = request.POST.get(field_name)

                if not qty_str or qty_str.strip() == "":
                    continue

                qty = Decimal(qty_str)
                if qty <= 0:
                    # No permitir negativos o cero
                    continue

                IngredientStockAdjustment.objects.create(
                    ingredient=ingredient,
                    quantity=qty,
                    reason=f"Ingreso por compra (registrado por {request.user.username})",
                )
                count += 1

            if count > 0:
                messages.success(request, f"✅ Se registraron {count} compras de ingredientes correctamente.")
            else:
                messages.info(request, "No se registró ninguna compra.")
        return redirect("purchase_ingredients")

    return render(request, "purchase_ingredients.html", {"ingredients": ingredients})

# -------------------------
# 7. Exportar a CSV
# -------------------------
@login_required
def export_orders_csv(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="comandas_{timezone.now().date()}.csv"'

    writer = csv.writer(response)
    writer.writerow(["Fecha", "Hora", "Comanda", "Mesa", "Producto", "Cantidad", "Precio", "Monto"])

    orders = Order.objects.all().order_by("-created_at")
    for order in orders:
        for item in order.orderitem_set.all():
            writer.writerow([
                order.created_at.date(),
                order.created_at.time().strftime("%H:%M"),
                order.id,
                order.table.name if order.table else "Sin mesa",
                item.product.name,
                item.quantity,
                item.product.price,
                item.get_total(),
            ])

    return response
