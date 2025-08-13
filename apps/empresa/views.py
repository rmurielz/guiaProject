import logging
from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse
from django.contrib import messages
from django.views.generic import CreateView
from django.views import View
from django.urls import reverse, reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from .models import Empresa
from .forms import EmpresaForm

logger = logging.getLogger(__name__)

class EmpresaCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """
    Vista para crear una nueva empresa.
    """
    model = Empresa
    form_class = EmpresaForm
    template_name = 'empresa/empresa_form.html'
    success_url = reverse_lazy('dashboard')
    permission_required = 'empresa.add_empresa'

    def get_context_data(self, **kwargs):
        """
        Asegura que el contexto necesario para el selector de ubicación esté presente.
        """
        context = super().get_context_data(**kwargs)
        # Esta línea es CRUCIAL para evitar el error de JavaScript que impide
        # que el selector de ubicación se cargue.
        context['ubicacion_inicial'] = None
        return context

    def form_valid(self, form):
        """
        Al crear la empresa, se asigna al usuario actual y, muy importante,
        se establece como la empresa activa en la sesión para una mejor
        experiencia de usuario.
        """
        empresa = form.save()
        empresa.usuarios.add(self.request.user)

        # UX Improvement: Auto-seleccionar la nueva empresa en la sesión.
        self.request.session['empresa_id'] = empresa.id
        self.request.session['empresa_nombre'] = empresa.nombre

        messages.success(self.request, f'Empresa "{empresa.nombre}" creada y seleccionada exitosamente.')
        return super().form_valid(form)

class SeleccionarEmpresaView(LoginRequiredMixin, View):
    """
    Vista segura (basada en POST) para que el usuario seleccione la empresa
    con la que quiere trabajar.
    """
    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        empresa_id = request.POST.get('empresa_id')
        if not empresa_id:
            messages.error(request, "No se seleccionó ninguna empresa.")
            return redirect('dashboard')

        try:
            # Seguridad: verificar que la empresa exista y que el usuario tenga acceso a ella.
            empresa = request.user.empresas.get(pk=empresa_id, activo=True)
            request.session['empresa_id'] = empresa.id
            request.session['empresa_nombre'] = empresa.nombre
            messages.success(request, f'Has cambiado a la empresa "{empresa.nombre}".')
        except Empresa.DoesNotExist:
            messages.error(request, "La empresa seleccionada no es válida o no tienes acceso a ella.")

        return redirect('dashboard')
