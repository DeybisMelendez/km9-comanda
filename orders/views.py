import csv
from datetime import datetime, time, timedelta
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import F, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models import (Ingredient, IngredientMovement, Order, OrderItem, Product,
                     ProductCategory, Table)

# ==========================
# 🔐 UTILIDADES Y PERMISOS
# ==========================

def is_encargado(user):
    """Verifica si el usuario pertenece al grupo Encargado."""
    return user.groups.filter(name="Encargado").exists()


def parse_date_range(request):
    """Obtiene el rango de fechas desde GET o usa el día actual."""
    date_format = "%Y-%m-%dT%H:%M"
    start_str = request.GET.get("start")
    end_str = request.GET.get("end")

    if start_str and end_str:
        start = datetime.strptime(start_str, date_format)
        end = datetime.strptime(end_str, date_format)
    else:
        today = datetime.today().date()
        start = datetime.combine(today, time.min)
        end = datetime.combine(today, time.max)
    return start, end


# ==========================
# 🪑 MESAS Y COMANDAS
# ==========================

@login_required
def table_list(request):
    """Muestra todas las mesas y su total pendiente."""
    tables = Table.objects.all().order_by("name")
    table_data = []

    for table in tables:
        total_due = (
            Order.objects.filter(table=table, is_paid=False)
            .annotate(total=Sum(F("orderitem__quantity") * F("orderitem__product__price")))
            .aggregate(total=Sum("total"))["total"]
            or 0
        )
        table_data.append({"table": table, "total_due": total_due})

    return render(request, "table_list.html", {"table_data": table_data})


@login_required
def table_orders(request, table_id):
    """Lista de comandas activas de una mesa."""
    table = get_object_or_404(Table, id=table_id)
    orders = (
        Order.objects.filter(table=table, is_paid=False)
        .prefetch_related("orderitem_set__product")
        .order_by("-created_at")
    )
    return render(request, "table_orders.html", {"table": table, "orders": orders})


@login_required
def mark_table_paid(request, table_id):
    """Marca todas las órdenes no pagadas de una mesa como pagadas."""
    table = get_object_or_404(Table, id=table_id)
    unpaid = Order.objects.filter(table=table, is_paid=False)

    if not unpaid.exists():
        messages.info(request, f"ℹ️ No hay comandas pendientes para {table.name}.")
    else:
        count = unpaid.update(is_paid=True)
        messages.success(request, f"✅ {count} comandas de la mesa {table.name} marcadas como pagadas.")

    return redirect("table_list")


# ==========================
# 🍽️ CREACIÓN Y DETALLE DE COMANDAS
# ==========================

@login_required
def create_order(request, table_id):
    """Crea una nueva comanda para una mesa."""
    table = get_object_or_404(Table, id=table_id)
    products = Product.objects.all().order_by("category__name", "name")
    categories = ProductCategory.objects.all().order_by("name")
    context = {"table": table, "products": products, "categories": categories}

    if request.method == "POST":
        order = Order.objects.create(table=table, user=request.user)
        created_items = 0

        for key, value in request.POST.items():
            if key.startswith("product_") and value.isdigit() and int(value) > 0:
                product = get_object_or_404(Product, id=key.split("_")[1])
                OrderItem.objects.create(order=order, product=product, quantity=int(value))
                created_items += 1

        if created_items:
            messages.success(request, f"✅ Comanda #{order.id} creada con {created_items} productos.")
            context['order'] = order
            return render(request, "create_order.html", context)

        order.delete()
        messages.warning(request, "⚠️ No se seleccionaron productos.")
        return redirect("create_order", table_id=table.id)

    return render(request, "create_order.html", context)


@login_required
def order_detail(request, order_id):
    """Muestra el detalle de una comanda."""
    order = get_object_or_404(Order, id=order_id)
    items = order.orderitem_set.select_related("product")

    if request.method == "POST" and request.POST.get("action") == "mark_paid":
        if not order.is_paid:
            order.is_paid = True
            order.save()
            messages.success(request, f"✅ Comanda #{order.id} marcada como pagada.")
        else:
            messages.info(request, f"ℹ️ La comanda #{order.id} ya estaba pagada.")
        return redirect("table_list")

    return render(request, "order_detail.html", {"order": order, "items": items, "total": order.get_total()})


@login_required
@user_passes_test(is_encargado)
def edit_order(request, order_id):
    """Permite editar una comanda (mesa, usuario, pagada)."""
    order = get_object_or_404(Order, id=order_id)
    tables = Table.objects.all().order_by("name")
    users = User.objects.all().order_by("username")

    if request.method == "POST":
        order.table_id = request.POST.get("table") or None
        order.user_id = request.POST.get("user") or None
        order.is_paid = request.POST.get("is_paid") == "on"
        order.save()
        messages.success(request, f"✅ Comanda #{order.id} actualizada correctamente.")
        return redirect("order_detail", order_id=order.id)

    return render(request, "edit_order.html", {"order": order, "tables": tables, "users": users})


@login_required
def print_order(request, order_id):
    """Vista de impresión de comanda."""
    order = get_object_or_404(Order, id=order_id)
    items = order.orderitem_set.select_related("product").all()

    if not items.exists():
        messages.warning(request, f"⚠️ La comanda #{order.id} no tiene productos.")

    return render(request, "print_order.html", {"order": order, "items": items, "total": order.get_total()})


# ==========================
# 🕒 HISTORIAL Y REPORTES
# ==========================

@login_required
def order_history(request):
    """Muestra comandas de un día específico."""
    days_ago = int(request.GET.get("days_ago", 0))
    target_date = datetime.now() - timedelta(days=days_ago)

    orders = Order.objects.filter(created_at__date=target_date).select_related("table", "user").order_by("-created_at")
    total = orders.count()
    paid = orders.filter(is_paid=True).count()

    return render(request, "order_history.html", {
        "orders": orders,
        "target_date": target_date,
        "days_ago": days_ago,
        "prev_days_ago": days_ago + 1,
        "next_days_ago": max(days_ago - 1, 0),
    })


@login_required
@user_passes_test(is_encargado)
def daily_report(request):
    """Reporte diario de ventas."""
    days_ago = int(request.GET.get("days_ago", 0))
    target_date = timezone.now().date() - timedelta(days=days_ago)

    orders = Order.objects.filter(created_at__date=target_date, is_paid=True).prefetch_related("orderitem_set__product")
    summary, total_sales = {}, Decimal("0")

    for order in orders:
        for item in order.orderitem_set.all():
            name, price = item.product.name, item.product.price
            subtotal = item.quantity * price
            total_sales += subtotal

            summary.setdefault(name, {"qty": 0, "price": price, "subtotal": 0})
            summary[name]["qty"] += item.quantity
            summary[name]["subtotal"] += subtotal

    messages.info(request, f"📊 Ventas del {target_date}: {total_sales:.2f} total.")
    return render(request, "daily_report.html", {
        "orders": orders,
        "product_summary": summary,
        "target_date": target_date,
        "days_ago": days_ago,
        "prev_days_ago": days_ago + 1,
        "next_days_ago": max(days_ago - 1, 0),
        "total_sales": total_sales,
    })


# ==========================
# 🧾 INVENTARIO Y MOVIMIENTOS
# ==========================

@login_required
@user_passes_test(is_encargado)
def inventory_movement(request):
    """Ajustes de inventario físico."""
    ingredients = Ingredient.objects.all().order_by("name")

    if request.method == "POST":
        note = request.POST.get("note", "").strip()
        count = 0
        with transaction.atomic():
            for ing in ingredients:
                found_str = request.POST.get(f"found_{ing.id}")
                if not found_str:
                    continue
                try:
                    found_qty = Decimal(found_str)
                except Exception:
                    messages.error(request, f"❌ Valor inválido para {ing.name}.")
                    continue
                diff = found_qty - ing.stock_quantity
                if diff != 0:
                    IngredientMovement.objects.create(
                        ingredient=ing, quantity=diff, user=request.user,
                        reason=f"Ajuste por inventario físico. {note}"
                    )
                    count += 1
        if count:
            messages.success(request, f"✅ {count} ajustes aplicados.")
        else:
            messages.info(request, "ℹ️ No se realizaron ajustes.")
    return render(request, "inventory.html", {"ingredients": ingredients})


@login_required
@user_passes_test(is_encargado)
def purchase_ingredients(request):
    """Registra compras de ingredientes."""
    ingredients = Ingredient.objects.all().order_by("name")

    if request.method == "POST":
        count = 0
        with transaction.atomic():
            for ing in ingredients:
                qty_str = request.POST.get(f"purchase_{ing.id}")
                if not qty_str:
                    continue
                try:
                    qty = Decimal(qty_str)
                except Exception:
                    messages.error(request, f"❌ Cantidad inválida para {ing.name}.")
                    continue
                if qty > 0:
                    IngredientMovement.objects.create(
                        ingredient=ing, quantity=qty, user=request.user, reason="Compra de ingredientes"
                    )
                    count += 1
        messages.success(request, f"✅ {count} compras registradas.") if count else messages.info(request, "ℹ️ No se registró ninguna compra.")
        return redirect("purchase_ingredients")

    return render(request, "purchase_ingredients.html", {"ingredients": ingredients})


@login_required
@user_passes_test(is_encargado)
def report_inventory(request):
    """Muestra el estado actual del inventario."""
    ingredients = Ingredient.objects.all().order_by("name")
    total = ingredients.count()
    return render(request, "report_inventory.html", {"ingredients": ingredients, "total_items": total})


@login_required
@user_passes_test(is_encargado)
def export_inventory_csv(request):
    """Exporta el inventario actual a CSV."""
    ingredients = Ingredient.objects.all().order_by("name")

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="inventario_{datetime.now():%Y%m%d_%H%M}.csv"'

    writer = csv.writer(response)
    writer.writerow(["Ingrediente", "Cantidad", "Unidad"])
    for i in ingredients:
        writer.writerow([i.name, i.stock_quantity, getattr(i, "unit", "—")])
    return response


# ==========================
# 💾 REPORTES CSV
# ==========================

@login_required
@user_passes_test(is_encargado)
def report_orders(request):
    """Reporte de comandas por rango de fechas."""
    start, end = parse_date_range(request)
    items = OrderItem.objects.filter(order__created_at__range=(start, end)).select_related(
        "order", "product", "order__table", "order__user"
    )
    return render(request, "report_orders.html", {"order_items": items, "start": start, "end": end})


@login_required
@user_passes_test(is_encargado)
def export_orders_csv(request):
    """Exporta las comandas a CSV."""
    start, end = parse_date_range(request)
    items = OrderItem.objects.filter(order__created_at__range=(start, end)).select_related(
        "order", "product", "order__table", "order__user"
    )

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="comandas_{datetime.now():%Y%m%d_%H%M}.csv"'

    writer = csv.writer(response)
    writer.writerow(["Fecha", "Comanda", "Mesero", "Mesa", "Cantidad", "Producto", "Precio", "Total"])
    for i in items:
        writer.writerow([
            i.order.created_at.strftime("%Y-%m-%d %H:%M"),
            i.order.id,
            i.order.user.username if i.order.user else "—",
            i.order.table.name if i.order.table else "—",
            i.quantity, i.product.name, i.product.price, i.get_total(),
        ])
    return response


@login_required
@user_passes_test(is_encargado)
def report_movements(request):
    """Lista los movimientos de inventario."""
    start, end = parse_date_range(request)
    moves = IngredientMovement.objects.filter(created_at__range=(start, end)).select_related("ingredient")
    return render(request, "report_movements.html", {"movements": moves, "start": start, "end": end})


@login_required
@user_passes_test(is_encargado)
def export_movements_csv(request):
    """Exporta los movimientos de inventario a CSV."""
    start, end = parse_date_range(request)
    moves = IngredientMovement.objects.filter(created_at__range=(start, end)).select_related("ingredient")

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="movimientos_{datetime.now():%Y%m%d_%H%M}.csv"'

    writer = csv.writer(response)
    writer.writerow(["Fecha", "Cantidad", "Ingrediente", "Razón", "Usuario"])
    for m in moves:
        writer.writerow([
            m.created_at.strftime("%Y-%m-%d %H:%M"),
            m.quantity,
            m.ingredient.name,
            m.reason or "—",
            m.user.username if m.user else "—",
        ])
    return response
