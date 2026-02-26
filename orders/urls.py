from django.urls import path

from . import views

urlpatterns = [
    path("", views.table_list, name="table_list"),
    path("mesa/<int:table_id>/", views.table_orders, name="table_orders"),
    path("mesa/<int:table_id>/pagar/", views.mark_table_paid, name="mark_table_paid"),
    path("mesa/<int:table_id>/nueva/", views.create_order, name="create_order"),
    path("orden/<int:order_id>/", views.order_detail, name="order_detail"),
    path("orden/<int:order_id>/editar/", views.edit_order, name="edit_order"),
    path("orden/<int:order_id>/imprimir/", views.print_order, name="print_order"),
    path("historial/", views.order_history, name="order_history"),
    path("reporte/", views.daily_report, name="daily_report"),
    path(
        "ingredientes/movimientos/", views.inventory_movement, name="inventory_movement"
    ),
    path(
        "ingredientes/compras/", views.purchase_ingredients, name="purchase_ingredients"
    ),
    # Reportes con filtro de fecha
    path("reportes/comandas/", views.report_orders, name="report_orders"),
    path(
        "reportes/movimiento-ingredientes/",
        views.report_movements,
        name="report_movements",
    ),
    path(
        "reportes/saldo-ingredientes/", views.report_inventory, name="report_inventory"
    ),
    path(
        "reportes/saldo-ingredientes/imprimir/",
        views.print_inventory_report,
        name="print_inventory_report",
    ),
    path(
        "reportes/ventas-producto/",
        views.sales_report_by_product,
        name="sales_report_by_product",
    ),
    # Descargas CSV
    path("reportes/comandas/csv/", views.export_orders_csv, name="export_orders_csv"),
    path(
        "reportes/movimiento-ingredientes/csv/",
        views.export_movements_csv,
        name="export_movements_csv",
    ),
    path(
        "reportes/saldo-ingredientes/csv/",
        views.export_inventory_csv,
        name="export_inventory_csv",
    ),
    path(
        "reportes/ventas-producto/csv/",
        views.export_sales_by_product_csv,
        name="export_sales_by_product_csv",
    ),
    # Gestión de productos
    path("productos/", views.product_list, name="product_list"),
    path("productos/nuevo/", views.product_create, name="product_create"),
    path("productos/<int:product_id>/editar/", views.product_edit, name="product_edit"),
    path(
        "productos/<int:product_id>/eliminar/",
        views.product_delete,
        name="product_delete",
    ),
    # Gestión de recetas
    path(
        "productos/<int:product_id>/recetas/",
        views.product_recipes,
        name="product_recipes",
    ),
    # Gestión de categorías de productos
    path("categorias/", views.category_list, name="category_list"),
    path("categorias/nueva/", views.category_create, name="category_create"),
    path(
        "categorias/<int:category_id>/editar/",
        views.category_edit,
        name="category_edit",
    ),
    path(
        "categorias/<int:category_id>/eliminar/",
        views.category_delete,
        name="category_delete",
    ),
    # Gestión de áreas de despacho
    path("areas-despacho/", views.dispatch_area_list, name="dispatch_area_list"),
    path(
        "areas-despacho/nueva/", views.dispatch_area_create, name="dispatch_area_create"
    ),
    path(
        "areas-despacho/<int:area_id>/editar/",
        views.dispatch_area_edit,
        name="dispatch_area_edit",
    ),
    path(
        "areas-despacho/<int:area_id>/eliminar/",
        views.dispatch_area_delete,
        name="dispatch_area_delete",
    ),
]
