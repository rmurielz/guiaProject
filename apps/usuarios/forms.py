from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from apps.empresa.models import Empresa
from django.contrib.auth.models import Permission

class CustomUserCreationForm(UserCreationForm):
    """
    Formulario para que el SUPERADMIN cree usuarios.
    Permite asignar empresas y designar administradores de empresa.
    """
    email = forms.EmailField(required=True, help_text="Requerido. Se usará para notificaciones.")
    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=True)
    is_staff = forms.BooleanField(
        label="Acceso al panel de Admin",
        required=False,
        help_text="Permite al usuario acceder al panel de administración de Django."
    )
    is_superuser = forms.BooleanField(
        label="Superusuario (Todos los permisos)",
        required=False,
        help_text="Otorga todos los permisos sin asignarlos explícitamente."
    )
    es_admin_empresa = forms.BooleanField(
        label="Administrador de Empresa",
        required=False,
        help_text="Permite al usuario gestionar otros usuarios y configuraciones de sus empresas asignadas."
    )
    empresas = forms.ModelMultipleChoiceField(
        queryset=Empresa.objects.filter(activo=True),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Empresas Asignadas",
        help_text="Selecciona las empresas a las que este usuario tendrá acceso."
    )

    class Meta(UserCreationForm.Meta):
        model = User
        # Limpiamos la meta. Los campos booleanos ya se manejan en el save()
        fields = UserCreationForm.Meta.fields + ('first_name', 'last_name', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Aplicar estilos CSS a todos los campos
        for field_name, field in self.fields.items():
            if field.widget.__class__.__name__ == 'CheckboxInput':
                field.widget.attrs.update({'class': 'form-check-input'})
            elif field.widget.__class__.__name__ == 'CheckboxSelectMultiple':
                # No aplicar form-control a CheckboxSelectMultiple
                pass
            elif field.widget.__class__.__name__ == 'PasswordInput':
                # Mantener el tipo password y aplicar form-control
                field.widget.attrs.update({'class': 'form-control'})
            elif field.widget.__class__.__name__ != 'CheckboxSelectMultiple':
                field.widget.attrs.update({'class': 'form-control'})

        # Personalizar labels y help_text de los campos de contraseña si es necesario
        self.fields['password1'].help_text = "Tu contraseña debe tener al menos 8 caracteres."
        self.fields['password2'].help_text = "Confirma tu contraseña ingresándola nuevamente."

    def clean_email(self):
        """Validar que el email sea único"""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Ya existe un usuario con este email.")
        return email

    def save(self, commit=True):
        """
        Sobrescribimos el método save para manejar explícitamente todos los campos,
        incluyendo los booleanos y la asignación automática de permisos.
        """
        user = super().save(commit=False)

        # Normalización de nombre y apellidos a formato Título
        user.first_name = self.cleaned_data.get('first_name', '').title()
        user.last_name = self.cleaned_data.get('last_name', '').title()
        user.email = self.cleaned_data.get('email', '')

        # Asignamos los valores de los campos booleanos desde el formulario
        user.is_staff = self.cleaned_data.get('is_staff', False)
        user.is_superuser = self.cleaned_data.get('is_superuser', False)

        if commit:
            user.save()

            # Verificar que el perfil existe antes de usar
            if hasattr(user, 'perfil'):
                user.perfil.es_admin_empresa = self.cleaned_data.get('es_admin_empresa', False)
                user.perfil.save()

            # Una vez que el usuario está guardado, podemos manejar las relaciones
            empresas = self.cleaned_data.get('empresas')
            if empresas:
                user.empresas.set(empresas)

            # Lógica clave: Asignar permisos si es staff pero no superusuario
            if user.is_staff and not user.is_superuser:
                # Damos todos los permisos sobre nuestras apps principales
                permissions = Permission.objects.filter(
                    content_type__app_label__in=['empresa', 'terceros', 'inventario', 'usuarios']
                )
                user.user_permissions.set(permissions)
            elif not user.is_staff:
                user.user_permissions.clear()  # Limpiamos por si se le quita el rol

        return user


class EmpresaUserCreationForm(UserCreationForm):
    """
    Formulario para que un Administrador de Empresa cree usuarios.
    Es más simple: no incluye la selección de empresa ni permisos globales.
    """
    email = forms.EmailField(required=True, help_text="Requerido. Se usará para notificaciones.")
    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('first_name', 'last_name', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field.widget.__class__.__name__ == 'PasswordInput':
                field.widget.attrs.update({'class': 'form-control'})
            elif field.widget.__class__.__name__ != 'CheckboxInput':
                field.widget.attrs.update({'class': 'form-control'})

    def clean_email(self):
        """Validar que el email sea único"""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Ya existe un usuario con este email.")
        return email

    def save(self, commit=True):
        """
        Sobrescribe save para normalizar el nombre y apellido a formato Título.
        """
        user = super().save(commit=False)
        user.first_name = self.cleaned_data.get('first_name', '').title()
        user.last_name = self.cleaned_data.get('last_name', '').title()
        user.email = self.cleaned_data.get('email', '')

        if commit:
            user.save()
        return user