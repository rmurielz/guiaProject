from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class CustomUserCreationForm(UserCreationForm):
    """
    Un formulario personalizado para crear usuarios, añadiendo campos
    para permisos de "maestro" (staff/superuser).
    """
    email = forms.EmailField(required=True, help_text="Requerido. Se usará para notificaciones.")
    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=True)
    is_staff = forms.BooleanField(label="Acceso al panel de Admin", required=False, help_text="Permite al usuario acceder al panel de administración de Django.")
    is_superuser = forms.BooleanField(label="Superusuario (Todos los permisos)", required=False, help_text="Otorga todos los permisos sin asignarlos explícitamente.")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('first_name', 'last_name', 'email', 'is_staff', 'is_superuser')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})
            if field_name == 'is_staff' or field_name == 'is_superuser':
                field.widget.attrs.update({'class': 'form-check-input'})