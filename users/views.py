"""
Vistas para gestión de usuarios.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render

from users.forms import UserCreateForm, UserEditForm
from users.utils import is_admin


@login_required
@user_passes_test(is_admin)
def user_list(request):
    """Lista todos los usuarios con sus grupos."""
    users = User.objects.all().order_by("username").prefetch_related("groups")
    return render(request, "users/user_list.html", {"users": users})


@login_required
@user_passes_test(is_admin)
def user_create(request):
    """Crea un nuevo usuario."""
    if request.method == "POST":
        form = UserCreateForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(
                request, f"✅ Usuario '{user.username}' creado exitosamente."
            )
            return redirect("user_list")
    else:
        form = UserCreateForm()

    return render(
        request,
        "users/user_form.html",
        {"form": form, "title": "Crear Usuario", "submit_label": "Crear Usuario"},
    )


@login_required
@user_passes_test(is_admin)
def user_edit(request, user_id):
    """Edita un usuario existente."""
    user = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        form = UserEditForm(request.POST, instance=user)
        if form.is_valid():
            user = form.save()
            messages.success(
                request, f"✅ Usuario '{user.username}' actualizado exitosamente."
            )
            return redirect("user_list")
    else:
        form = UserEditForm(instance=user)

    return render(
        request,
        "users/user_form.html",
        {
            "form": form,
            "title": "Editar Usuario",
            "submit_label": "Guardar Cambios",
            "user": user,
        },
    )
