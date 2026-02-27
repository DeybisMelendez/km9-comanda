"""
Utilidades para gestión de usuarios, roles y permisos.
"""

from django.contrib.auth.models import Group


def is_mesero(user):
    """Verifica si el usuario pertenece al grupo Mesero."""
    if user.is_superuser:
        return True
    return user.groups.filter(name="Mesero").exists()


def is_encargado(user):
    """Verifica si el usuario pertenece al grupo Encargado o Admin."""
    if user.is_superuser:
        return True
    return user.groups.filter(name__in=["Encargado", "Admin"]).exists()


def is_admin(user):
    """Verifica si el usuario pertenece al grupo Admin."""
    if user.is_superuser or user.is_staff:
        return True
    return user.groups.filter(name="Admin").exists()


def has_valid_role(user):
    """Verifica si el usuario tiene un rol válido (Mesero, Encargado, Admin) o es superusuario."""
    if user.is_superuser:
        return True
    return user.groups.filter(name__in=["Mesero", "Encargado", "Admin"]).exists()


def create_default_groups():
    """Crea los grupos predeterminados si no existen."""
    group_names = ["Mesero", "Encargado", "Admin"]
    for name in group_names:
        Group.objects.get_or_create(name=name)
