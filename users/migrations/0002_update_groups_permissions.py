"""
Migración para actualizar grupos y permisos fijos.
Reemplaza los grupos antiguos (Mesero, Encargado, Admin) por los nuevos:
Servicio, Supervisor, Administrador, Cocinero, Cajero.
Asigna permisos predefinidos a cada grupo.
"""

from django.db import migrations


def rename_and_create_groups(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")

    # Mapeo de renombramiento (viejo -> nuevo)
    rename_map = {
        "Mesero": "Servicio",
        "Encargado": "Supervisor",
        "Admin": "Administrador",
    }

    # Crear o renombrar grupos existentes
    for old_name, new_name in rename_map.items():
        try:
            group = Group.objects.get(name=old_name)
            group.name = new_name
            group.save()
        except Group.DoesNotExist:
            # Si no existe el grupo viejo, crear el nuevo
            Group.objects.get_or_create(name=new_name)

    # Grupos nuevos que no tienen equivalente viejo
    new_groups = ["Cocinero", "Cajero"]
    for name in new_groups:
        Group.objects.get_or_create(name=name)

    # Definición de permisos por grupo (codename sin app)
    # Nota: los permisos de la app 'orders' tienen prefijo 'orders.'
    # y los de 'auth' tienen prefijo 'auth.'
    group_permissions = {
        "Servicio": [
            "view_table",
            "view_productcategory",
            "view_dispatcharea",
            "view_warehouse",
            "view_product",
            "view_ingredient",
            "view_productingredient",
            "view_ingredientmovement",
            "view_order",
            "view_orderitem",
            "add_order",
            "change_order",
            "add_orderitem",
            "change_orderitem",
        ],
        "Supervisor": [
            "add_table",
            "change_table",
            "delete_table",
            "view_table",
            "add_productcategory",
            "change_productcategory",
            "delete_productcategory",
            "view_productcategory",
            "add_dispatcharea",
            "change_dispatcharea",
            "delete_dispatcharea",
            "view_dispatcharea",
            "add_warehouse",
            "change_warehouse",
            "delete_warehouse",
            "view_warehouse",
            "add_product",
            "change_product",
            "delete_product",
            "view_product",
            "add_ingredient",
            "change_ingredient",
            "delete_ingredient",
            "view_ingredient",
            "add_productingredient",
            "change_productingredient",
            "delete_productingredient",
            "view_productingredient",
            "add_ingredientmovement",
            "change_ingredientmovement",
            "delete_ingredientmovement",
            "view_ingredientmovement",
            "add_order",
            "change_order",
            "delete_order",
            "view_order",
            "add_orderitem",
            "change_orderitem",
            "delete_orderitem",
            "view_orderitem",
        ],
        "Administrador": [
            # Todos los permisos de Supervisor más usuarios y grupos
            "add_table",
            "change_table",
            "delete_table",
            "view_table",
            "add_productcategory",
            "change_productcategory",
            "delete_productcategory",
            "view_productcategory",
            "add_dispatcharea",
            "change_dispatcharea",
            "delete_dispatcharea",
            "view_dispatcharea",
            "add_warehouse",
            "change_warehouse",
            "delete_warehouse",
            "view_warehouse",
            "add_product",
            "change_product",
            "delete_product",
            "view_product",
            "add_ingredient",
            "change_ingredient",
            "delete_ingredient",
            "view_ingredient",
            "add_productingredient",
            "change_productingredient",
            "delete_productingredient",
            "view_productingredient",
            "add_ingredientmovement",
            "change_ingredientmovement",
            "delete_ingredientmovement",
            "view_ingredientmovement",
            "add_order",
            "change_order",
            "delete_order",
            "view_order",
            "add_orderitem",
            "change_orderitem",
            "delete_orderitem",
            "view_orderitem",
            # Permisos de auth
            "add_user",
            "change_user",
            "delete_user",
            "view_user",
            "add_group",
            "change_group",
            "delete_group",
            "view_group",
        ],
        "Cocinero": [
            "view_table",
            "view_productcategory",
            "view_dispatcharea",
            "view_warehouse",
            "view_product",
            "view_ingredient",
            "view_productingredient",
            "view_ingredientmovement",
            "view_order",
            "view_orderitem",
        ],
        "Cajero": [
            "view_table",
            "view_product",
            "view_order",
            "view_orderitem",
            "change_order",
        ],
    }

    # Asignar permisos a cada grupo
    for group_name, perm_codenames in group_permissions.items():
        group = Group.objects.get(name=group_name)
        permissions = []
        for codename in perm_codenames:
            # Determinar app_label
            if codename in [
                "add_user",
                "change_user",
                "delete_user",
                "view_user",
                "add_group",
                "change_group",
                "delete_group",
                "view_group",
            ]:
                app_label = "auth"
            else:
                app_label = "orders"
            try:
                perm = Permission.objects.get(
                    codename=codename, content_type__app_label=app_label
                )
                permissions.append(perm)
            except Permission.DoesNotExist:
                # Si no existe el permiso, ignorar (puede que no se haya creado aún)
                # En una migración posterior se crearán los permisos automáticamente
                pass
        group.permissions.set(permissions)
        group.save()


def reverse_groups(apps, schema_editor):
    """Revierte los cambios: restaura grupos antiguos y elimina nuevos."""
    Group = apps.get_model("auth", "Group")
    # Eliminar los nuevos grupos
    Group.objects.filter(
        name__in=["Servicio", "Supervisor", "Administrador", "Cocinero", "Cajero"]
    ).delete()
    # Restaurar grupos antiguos (si se eliminaron)
    old_groups = ["Mesero", "Encargado", "Admin"]
    for name in old_groups:
        Group.objects.get_or_create(name=name)


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(rename_and_create_groups, reverse_groups),
    ]
