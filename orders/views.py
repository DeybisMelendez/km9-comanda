from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.utils import timezone
from django.contrib.auth.models import User
from django.db import transaction
from decimal import Decimal
from datetime import datetime, timedelta
import csv
from .models import (
    Table, Product, ProductCategory,Order, OrderItem,
    Ingredient, IngredientMovement
)
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, F
from .models import Table, Order, OrderItem
from django.contrib.auth.decorators import user_passes_test

def is_encargado(user):
    return user.groups.filter(name='Encargado').exists()

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
def print_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    items = OrderItem.objects.filter(order=order)

    return render(request, "print_order.html", {
        "order": order,
        "items": items,
        "total": order.get_total(),
    })

@login_required
def create_order(request, table_id):
    table = get_object_or_404(Table, id=table_id)
    products = Product.objects.all().order_by("category__name", "name")
    categories = ProductCategory.objects.all().order_by("name")

    if request.method == "POST":
        order = Order.objects.create(table=table, user=request.user)
        for key, value in request.POST.items():
            if key.startswith("product_") and int(value) > 0:
                product_id = key.split("_")[1]
                product = Product.objects.get(id=product_id)
                OrderItem.objects.create(order=order, product=product, quantity=int(value))
        messages.success(request, "Comanda creada con éxito.")
        return render(request, "create_order.html", {
            "table": table,
            "products": products,
            "categories": categories,
            "order": order,
        })

    return render(request, "create_order.html", {
        "table": table,
        "products": products,
        "categories": categories,
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
@user_passes_test(is_encargado)
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
    # Obtener parámetro GET days_ago (por defecto 0)
    days_ago = int(request.GET.get("days_ago", 0))

    # Calcular la fecha objetivo
    target_date = timezone.now().date() - timedelta(days=days_ago)

    # Filtrar comandas por fecha específica
    orders = Order.objects.filter(created_at__date=target_date).order_by("-created_at")

    # Calcular días anterior y siguiente (limitando el siguiente a 0 = hoy)
    prev_days_ago = days_ago + 1
    next_days_ago = max(days_ago - 1, 0)

    context = {
        "orders": orders,
        "target_date": target_date,
        "days_ago": days_ago,
        "prev_days_ago": prev_days_ago,
        "next_days_ago": next_days_ago,
    }

    return render(request, "order_history.html", context)

# -------------------------
# 5. Reporte de Ventas del Día
# -------------------------
@login_required
@user_passes_test(is_encargado)
def daily_report(request):
    days_ago = int(request.GET.get("days_ago", 0))
    target_date = timezone.now().date() - timedelta(days=days_ago)

    # Filtrar órdenes pagadas
    orders = Order.objects.filter(
        created_at__date=target_date,
        is_paid=True
    ).order_by("-created_at")

    # Totales y resumen por producto (cantidad y subtotal)
    product_summary = {}
    total_sales = 0
    for order in orders:
        for item in order.orderitem_set.all():
            if item.product.name not in product_summary:
                product_summary[item.product.name] = {
                    "qty": 0,
                    "price": item.product.price,
                    "subtotal": 0
                }
            product_summary[item.product.name]["qty"] += item.quantity
            product_summary[item.product.name]["subtotal"] += item.quantity * item.product.price
            total_sales += item.quantity * item.product.price

    prev_days_ago = days_ago + 1
    next_days_ago = max(days_ago - 1, 0)

    context = {
        "orders": orders,
        "target_date": target_date,
        "days_ago": days_ago,
        "prev_days_ago": prev_days_ago,
        "next_days_ago": next_days_ago,
        "total_sales": total_sales,
        "product_summary": product_summary,
    }

    return render(request, "daily_report.html", context)

# -------------------------
# 6. Ajustes / Compras de Inventario
# -------------------------
@login_required
@user_passes_test(is_encargado)
def inventory_movement(request):
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
                    IngredientMovement.objects.create(
                        ingredient=ingredient,
                        quantity=diff,
                        user=request.user,
                        reason=f"Ajuste por inventario físico (hecho por {request.user.username})",
                    )

            messages.success(request, "✅ Ajustes de inventario aplicados correctamente.")

    return render(request, "inventory.html", {"ingredients": ingredients})

@login_required
@user_passes_test(is_encargado)
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
                IngredientMovement.objects.create(
                    ingredient=ingredient,
                    quantity=qty,
                    user=request.user,
                    reason="Compra de ingredientes"
                )
                count += 1

            if count > 0:
                messages.success(request, f"✅ Se registraron {count} compras de ingredientes correctamente.")
            else:
                messages.info(request, "No se registró ninguna compra.")
        return redirect("purchase_ingredients")

    return render(request, "purchase_ingredients.html", {"ingredients": ingredients})


def parse_date_range(request):
    """Helper para obtener rango de fechas desde GET."""
    date_format = "%Y-%m-%dT%H:%M"
    start_str = request.GET.get("start")
    end_str = request.GET.get("end")

    if start_str and end_str:
        start = datetime.strptime(start_str, date_format)
        end = datetime.strptime(end_str, date_format)
    else:
        # Por defecto, día actual completo
        today = timezone.now().date()
        start = timezone.make_aware(datetime.combine(today, datetime.min.time()))
        end = timezone.make_aware(datetime.combine(today, datetime.max.time()))
    return start, end

@login_required
@user_passes_test(is_encargado)
def report_orders(request):
    start, end = parse_date_range(request)
    order_items = OrderItem.objects.filter(order__created_at__range=(start, end)).select_related(
        "order", "product", "order__table", "order__user"
    )

    return render(request, "report_orders.html", {
        "order_items": order_items,
        "start": start,
        "end": end,
    })


@login_required
@user_passes_test(is_encargado)
def export_orders_csv(request):
    start, end = parse_date_range(request)
    order_items = OrderItem.objects.filter(order__created_at__range=(start, end)).select_related(
        "order", "product", "order__table", "order__user"
    )

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="reporte_comandas.csv"'

    writer = csv.writer(response)
    writer.writerow(["Fecha y hora", "No de Comanda", "Mesero", "Mesa", "Cantidad", "Producto", "Precio", "Monto"])

    for item in order_items:
        writer.writerow([
            item.order.created_at.strftime("%Y-%m-%d %H:%M"),
            item.order.id,
            item.order.user.username if item.order.user else "—",
            item.order.table.name if item.order.table else "—",
            item.quantity,
            item.product.name,
            item.product.price,
            item.get_total(),
        ])

    return response

@login_required
@user_passes_test(is_encargado)
def report_movements(request):
    start, end = parse_date_range(request)
    movements = IngredientMovement.objects.filter(created_at__range=(start, end)).select_related("ingredient")

    return render(request, "report_movements.html", {
        "movements": movements,
        "start": start,
        "end": end,
    })


@login_required
@user_passes_test(is_encargado)
def export_movements_csv(request):
    start, end = parse_date_range(request)
    movements = IngredientMovement.objects.filter(created_at__range=(start, end)).select_related("ingredient")

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="reporte_ajustes.csv"'

    writer = csv.writer(response)
    writer.writerow(["Fecha y hora", "Valor del ajuste", "Ingrediente", "Razón", "Usuario"])

    for mov in movements:
        writer.writerow([
            mov.created_at.strftime("%Y/%m/%d %H:%M"),
            mov.quantity,
            mov.ingredient.name,
            mov.reason or "—",
            mov.user.username if mov.user else "—",
        ])

    return response
