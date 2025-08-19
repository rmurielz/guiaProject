from django.contrib.auth.models import User
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin, UserPassesTestMixin
from apps.core.mixins import EmpresaRequiredMixin
from .forms import CustomUserCreationForm, EmpresaUserCreationForm


class SuperuserRequiredMixin(UserPassesTestMixin):
    """Asegura que solo el superusuario pueda acceder a esta vista."""
    def test_func(self):
        return self.request.user.is_superuser


class UserCreateView(SuperuserRequiredMixin, CreateView):
    """
    Vista para que el SUPERADMIN cree usuarios. Usa el formulario completo.
    """
    model = User
    form_class = CustomUserCreationForm
    template_name = 'usuarios/usuario_form.html'
    success_url = reverse_lazy('dashboard') # O a una futura lista de usuarios

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Crear Nuevo Usuario'
        return context

    def form_valid(self, form):
        # Toda la lógica de guardado (usuario, empresas, permisos)
        # ahora está encapsulada en el método save() del formulario.
        form.save()
        messages.success(self.request, f"Usuario '{form.cleaned_data.get('username')}' creado exitosamente.")
        return redirect(self.success_url)


class AdminEmpresaRequiredMixin(UserPassesTestMixin):
    """
    Asegura que el usuario sea un administrador de empresa.
    Asume que el modelo Perfil ya está implementado.
    """
    def test_func(self):
        return hasattr(self.request.user, 'perfil') and self.request.user.perfil.es_admin_empresa


class EmpresaUserCreateView(EmpresaRequiredMixin, AdminEmpresaRequiredMixin, CreateView):
    """
    Vista para que un Administrador de Empresa cree usuarios para SU empresa.
    """
    model = User
    form_class = EmpresaUserCreationForm
    template_name = 'usuarios/usuario_form.html' # Reutilizamos la plantilla
    success_url = reverse_lazy('dashboard') # O a una futura lista de usuarios de la empresa

    def form_valid(self, form):
        user = form.save()
        # Asignación automática a la empresa activa del administrador
        user.empresas.add(self.empresa_activa)
        messages.success(self.request, f"Usuario '{user.username}' creado para la empresa {self.empresa_activa.nombre}.")
        return redirect(self.success_url)
