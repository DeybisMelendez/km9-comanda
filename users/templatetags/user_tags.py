"""
Etiquetas de plantilla para verificación de grupos y permisos.
Reemplaza a user_extras.py con un enfoque más correcto.
"""

from django import template

from users.utils import is_admin  # compatibilidad
from users.utils import is_encargado  # compatibilidad
from users.utils import is_mesero  # compatibilidad
from users.utils import (is_administrador, is_cajero, is_cocinero, is_servicio,
                         is_supervisor)

register = template.Library()


# ==========================
# 🔍 FILTROS DE GRUPOS
# ==========================


@register.filter(name="is_servicio")
def filter_is_servicio(user):
    """Verifica si el usuario pertenece al grupo Servicio."""
    return is_servicio(user)


@register.filter(name="is_supervisor")
def filter_is_supervisor(user):
    """Verifica si el usuario pertenece al grupo Supervisor."""
    return is_supervisor(user)


@register.filter(name="is_administrador")
def filter_is_administrador(user):
    """Verifica si el usuario pertenece al grupo Administrador."""
    return is_administrador(user)


@register.filter(name="is_cocinero")
def filter_is_cocinero(user):
    """Verifica si el usuario pertenece al grupo Cocinero."""
    return is_cocinero(user)


@register.filter(name="is_cajero")
def filter_is_cajero(user):
    """Verifica si el usuario pertenece al grupo Cajero."""
    return is_cajero(user)


# Filtros de compatibilidad (mantener para templates existentes)
@register.filter(name="is_mesero")
def filter_is_mesero(user):
    """Compatibilidad: alias de is_servicio."""
    return is_mesero(user)


@register.filter(name="is_encargado")
def filter_is_encargado(user):
    """Compatibilidad: alias de is_supervisor o is_administrador."""
    return is_encargado(user)


@register.filter(name="is_admin")
def filter_is_admin(user):
    """Compatibilidad: alias de is_administrador."""
    return is_admin(user)


# ==========================
# 🛡️ FILTROS DE PERMISOS COMUNES
# ==========================


@register.filter(name="can_view_orders")
def filter_can_view_orders(user):
    """Verifica si el usuario puede ver órdenes."""
    return user.has_perm("orders.view_order")


@register.filter(name="can_create_orders")
def filter_can_create_orders(user):
    """Verifica si el usuario puede crear órdenes."""
    return user.has_perm("orders.add_order")


@register.filter(name="can_mark_paid")
def filter_can_mark_paid(user):
    """Verifica si el usuario puede marcar órdenes como pagadas."""
    return user.has_perm("orders.change_order")


@register.filter(name="can_manage_inventory")
def filter_can_manage_inventory(user):
    """Verifica si el usuario puede gestionar inventario."""
    return user.has_perm("orders.change_ingredient")


@register.filter(name="can_manage_products")
def filter_can_manage_products(user):
    """Verifica si el usuario puede gestionar productos."""
    return user.has_perm("orders.change_product")


@register.filter(name="can_manage_users")
def filter_can_manage_users(user):
    """Verifica si el usuario puede gestionar usuarios."""
    return user.has_perm("auth.change_user")


# ==========================
# 📋 FILTROS DE GRUPOS (compatibilidad)
# ==========================


@register.filter(name="has_group")
def filter_has_group(user, group_name):
    """Verifica si el usuario pertenece a un grupo específico."""
    return user.groups.filter(name=group_name).exists()


@register.filter(name="get_group")
def filter_get_group(user):
    """
    Devuelve el nombre del primer grupo al que pertenece el usuario.
    Si no pertenece a ninguno, devuelve None.
    """
    group = user.groups.first()
    return group.name if group else None
