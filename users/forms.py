"""
Formularios para gestión de usuarios.
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group, User


class UserCreateForm(UserCreationForm):
    """Formulario para crear un nuevo usuario."""

    first_name = forms.CharField(
        max_length=30,
        required=True,
        label="Nombre",
        widget=forms.TextInput(attrs={"placeholder": "Nombre"}),
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        label="Apellido",
        widget=forms.TextInput(attrs={"placeholder": "Apellido"}),
    )
    groups = forms.ModelChoiceField(
        queryset=Group.objects.filter(name__in=["Mesero", "Encargado", "Admin"]),
        required=True,
        label="Rol",
        help_text="Seleccione el rol del usuario",
    )

    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "groups",
            "password1",
            "password2",
        ]
        labels = {
            "username": "Nombre de usuario",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Agregar clase form__control a todos los widgets
        for field_name, field in self.fields.items():
            field.widget.attrs.update({"class": "form__control"})
            if field_name in ["username", "first_name", "last_name"]:
                field.widget.attrs.update({"placeholder": field.label})

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        if commit:
            user.save()
            user.groups.clear()
            user.groups.add(self.cleaned_data["groups"])
        return user


class UserEditForm(forms.ModelForm):
    """Formulario para editar un usuario existente."""

    first_name = forms.CharField(max_length=30, required=True, label="Nombre")
    last_name = forms.CharField(max_length=30, required=True, label="Apellido")
    groups = forms.ModelChoiceField(
        queryset=Group.objects.filter(name__in=["Mesero", "Encargado", "Admin"]),
        required=True,
        label="Rol",
    )
    password1 = forms.CharField(
        label="Nueva contraseña",
        widget=forms.PasswordInput,
        required=False,
        help_text="Deje vacío si no desea cambiar la contraseña.",
    )
    password2 = forms.CharField(
        label="Confirmar nueva contraseña",
        widget=forms.PasswordInput,
        required=False,
        help_text="Repita la nueva contraseña.",
    )

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "groups"]
        labels = {
            "username": "Nombre de usuario",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # Cargar el grupo actual del usuario (solo el primero)
            group = self.instance.groups.filter(
                name__in=["Mesero", "Encargado", "Admin"]
            ).first()
            if group:
                self.initial["groups"] = group

        # Agregar clase form__control a todos los widgets
        for field_name, field in self.fields.items():
            field.widget.attrs.update({"class": "form__control"})
            if field_name in ["username", "first_name", "last_name"]:
                field.widget.attrs.update({"placeholder": field.label})

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 or password2:
            if password1 != password2:
                raise forms.ValidationError("Las contraseñas no coinciden.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]

        # Actualizar contraseña si se proporcionó
        password = self.cleaned_data.get("password1")
        if password:
            user.set_password(password)

        if commit:
            user.save()
            # Actualizar grupo
            user.groups.clear()
            user.groups.add(self.cleaned_data["groups"])
        return user
