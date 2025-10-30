from django.urls import path
from . import views

urlpatterns = [
    path("", views.table_list, name="table_list"),
    path("mesa/<int:table_id>/", views.table_orders, name="table_orders"),
    path("mesa/<int:table_id>/pagar/", views.mark_table_paid, name="mark_table_paid"),
    path("mesa/<int:table_id>/nueva/", views.create_order, name="create_order"),
    path("orden/<int:order_id>/", views.order_detail, name="order_detail"),
    path("orden/<int:order_id>/editar/", views.edit_order, name="edit_order"),
    path("historial/", views.order_history, name="order_history"),
    path("reporte/", views.daily_report, name="daily_report"),
    path("inventario/ajustes/", views.inventory_adjustment, name="inventory_adjustment"),
    path("inventario/compras/", views.purchase_ingredients, name="purchase_ingredients"),
    path("exportar/csv/", views.export_orders_csv, name="export_orders_csv"),
]
