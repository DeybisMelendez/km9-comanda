from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.utils import timezone
import csv
from .models import (
    Table, Product, Order, OrderItem,
    Ingredient, IngredientStockAdjustment
)


# -------------------------
# 1. Selección de Mesa
# -------------------------
@login_required
def table_list(request):
    tables = Table.objects.all().order_by("name")
    return render(request, "table_list.html", {"tables": tables})


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
            order.status = "closed"
            order.save()
            messages.success(request, "Orden marcada como pagada.")
            return redirect("table_list")

    return render(request, "order_detail.html", {
        "order": order,
        "items": items,
        "total": order.get_total(),
    })


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
    orders = Order.objects.filter(created_at__date=today, status="closed")

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
def inventory_list(request):
    ingredients = Ingredient.objects.all().order_by("name")
    return render(request, "inventory_list.html", {"ingredients": ingredients})


@login_required
def add_stock_adjustment(request, ingredient_id):
    ingredient = get_object_or_404(Ingredient, id=ingredient_id)

    if request.method == "POST":
        qty = request.POST.get("quantity")
        reason = request.POST.get("reason", "Ajuste manual")
        IngredientStockAdjustment.objects.create(
            ingredient=ingredient,
            quantity=qty,
            reason=reason
        )
        messages.success(request, f"Ajuste aplicado a {ingredient.name}.")
        return redirect("inventory_list")

    return render(request, "add_stock_adjustment.html", {"ingredient": ingredient})


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
