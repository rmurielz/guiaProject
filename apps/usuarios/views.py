from django.contrib.auth.models import User
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from .forms import CustomUserCreationForm

class UserCreateView(PermissionRequiredMixin, CreateView):
    model = User
    form_class = CustomUserCreationForm
    template_name = 'usuarios/usuario_form.html'
    success_url = reverse_lazy('dashboard') # O a una futura lista de usuarios
    permission_required = 'auth.add_user'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Crear Nuevo Usuario'
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Usuario '{form.cleaned_data.get('username')}' creado exitosamente.")
        return super().form_valid(form)
