from django import template

register = template.Library()


@register.filter(name="get_group")
def get_group(user):
    """
    Devuelve el nombre del primer grupo al que pertenece el usuario.
    Si no pertenece a ninguno, devuelve None.
    """
    group = user.groups.first()
    return group.name if group else None


@register.filter(name="has_group")
def has_group(user, group_name):
    """Verifica si el usuario pertenece a un grupo"""
    return user.groups.filter(name=group_name).exists()


@register.filter(name="is_mesero")
def is_mesero(user):
    """Verifica si el usuario pertenece al grupo Mesero"""
    if user.is_superuser:
        return True
    return user.groups.filter(name="Mesero").exists()


@register.filter(name="is_encargado")
def is_encargado(user):
    """Verifica si el usuario pertenece al grupo Encargado o Admin"""
    if user.is_superuser:
        return True
    return user.groups.filter(name__in=["Encargado", "Admin"]).exists()


@register.filter(name="is_admin")
def is_admin(user):
    """Verifica si el usuario pertenece al grupo Admin"""
    if user.is_superuser or user.is_staff:
        return True
    return user.groups.filter(name="Admin").exists()
