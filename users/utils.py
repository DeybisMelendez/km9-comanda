"""
Utilidades para gestión de usuarios, roles y permisos.
"""

from users.permissions import (GROUP_ADMINISTRADOR, GROUP_CAJERO,
                               GROUP_COCINERO, GROUP_SERVICIO,
                               GROUP_SUPERVISOR)

# ==========================
# 🔍 VERIFICACIÓN DE GRUPOS
# ==========================


def is_servicio(user):
    """Verifica si el usuario pertenece al grupo Servicio."""
    if user.is_superuser:
        return True
    return user.groups.filter(name=GROUP_SERVICIO).exists()


def is_supervisor(user):
    """Verifica si el usuario pertenece al grupo Supervisor."""
    if user.is_superuser:
        return True
    return user.groups.filter(name=GROUP_SUPERVISOR).exists()


def is_administrador(user):
    """Verifica si el usuario pertenece al grupo Administrador."""
    if user.is_superuser or user.is_staff:
        return True
    return user.groups.filter(name=GROUP_ADMINISTRADOR).exists()


def is_cocinero(user):
    """Verifica si el usuario pertenece al grupo Cocinero."""
    if user.is_superuser:
        return True
    return user.groups.filter(name=GROUP_COCINERO).exists()


def is_cajero(user):
    """Verifica si el usuario pertenece al grupo Cajero."""
    if user.is_superuser:
        return True
    return user.groups.filter(name=GROUP_CAJERO).exists()


# Funciones de compatibilidad (mantener para vistas existentes)
def is_mesero(user):
    """Compatibilidad: alias de is_servicio."""
    return is_servicio(user)


def is_encargado(user):
    """Compatibilidad: alias de is_supervisor, is_administrador o is_cajero."""
    if user.is_superuser:
        return True
    return user.groups.filter(
        name__in=[GROUP_SUPERVISOR, GROUP_ADMINISTRADOR, GROUP_CAJERO]
    ).exists()


def is_admin(user):
    """Compatibilidad: alias de is_administrador."""
    return is_administrador(user)


# ==========================
# 🛡️ VERIFICACIÓN DE PERMISOS
# ==========================


def has_valid_role(user):
    """
    Verifica si el usuario tiene un rol válido (cualquiera de los grupos definidos)
    o es superusuario.
    """
    if user.is_superuser:
        return True
    valid_groups = [
        GROUP_SERVICIO,
        GROUP_SUPERVISOR,
        GROUP_ADMINISTRADOR,
        GROUP_COCINERO,
        GROUP_CAJERO,
    ]
    return user.groups.filter(name__in=valid_groups).exists()


def user_can_view_orders(user):
    """Verifica si el usuario puede ver órdenes."""
    return user.has_perm("orders.view_order")


def user_can_create_orders(user):
    """Verifica si el usuario puede crear órdenes."""
    return user.has_perm("orders.add_order")


def user_can_mark_paid(user):
    """Verifica si el usuario puede marcar órdenes como pagadas."""
    return user.has_perm("orders.change_order")


def user_can_manage_inventory(user):
    """Verifica si el usuario puede gestionar inventario."""
    return user.has_perm("orders.change_ingredient")


def user_can_manage_products(user):
    """Verifica si el usuario puede gestionar productos."""
    return user.has_perm("orders.change_product")


def user_can_manage_users(user):
    """Verifica si el usuario puede gestionar usuarios."""
    return user.has_perm("auth.change_user")


# ==========================
# 🏗️ CREACIÓN DE GRUPOS (para migraciones o setup)
# ==========================


def create_default_groups():
    """Crea los grupos predeterminados si no existen (usar desde migración)."""
    from users.permissions import create_groups_with_permissions

    create_groups_with_permissions()
