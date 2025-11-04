from django import template

register = template.Library()

@register.filter(name='get_group')
def get_group(user):
    """
    Devuelve el nombre del primer grupo al que pertenece el usuario.
    Si no pertenece a ninguno, devuelve None.
    """
    group = user.groups.first()
    return group.name if group else None

@register.filter(name='has_group')
def has_group(user, group_name):
    """Verifica si el usuario pertenece a un grupo"""
    return user.groups.filter(name=group_name).exists()

@register.filter(name='is_mesero')
def has_group(user):
    """Verifica si el usuario pertenece al grupo Mesero"""
    return user.groups.filter(name="Mesero").exists()

@register.filter(name='is_encargado')
def has_group(user):
    """Verifica si el usuario pertenece al grupo Encargado"""
    return user.groups.filter(name="Encargado").exists()

@register.filter(name='is_admin')
def has_group(user):
    """Verifica si el usuario pertenece al grupo Encargado"""
    return user.groups.filter(name="Admin").exists()