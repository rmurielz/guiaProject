from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from apps.core.mixins import EmpresaRequiredMixin
from .models import Bodega
from .forms import BodegaForm


class BodegaListView(EmpresaRequiredMixin, ListView):
    model = Bodega
    template_name = 'inventario/bodega_list.html'
    context_object_name = 'bodegas'
    paginate_by = 10

    def get_queryset(self):
        """Optimización para precargar datos relacionados y mostrar solo activos de la empresa seleccionada."""
        return Bodega.objects.filter(empresa=self.empresa_activa).select_related(
            'ciudad__division__pais', 'responsable'
        ).filter(activo=True).order_by('nombre')


class BodegaCreateView(EmpresaRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Bodega
    form_class = BodegaForm
    template_name = 'inventario/bodega_form.html'
    success_url = reverse_lazy('inventario:lista_bodegas')
    permission_required = 'inventario.add_bodega'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Crear Nueva Bodega'
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['empresa_id'] = self.empresa_activa.id
        return kwargs

    def form_valid(self, form):
        # Asignar la empresa activa de la sesión al nuevo objeto.
        form.instance.empresa = self.empresa_activa
        messages.success(self.request, f'Bodega "{form.instance.nombre}" creada exitosamente.')
        return super().form_valid(form)


class BodegaUpdateView(EmpresaRequiredMixin, UpdateView):
    model = Bodega
    form_class = BodegaForm
    template_name = 'inventario/bodega_form.html'
    success_url = reverse_lazy('inventario:lista_bodegas')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['empresa_id'] = self.empresa_activa.id
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Editar Bodega: {self.object.nombre}'

        # Preparar datos de ubicación para el frontend
        bodega = self.object
        if bodega.ciudad:
            context['ubicacion_inicial'] = {
                'pais': {'id': bodega.ciudad.division.pais.geoname_id, 'nombre': bodega.ciudad.division.pais.nombre, 'codigo': bodega.ciudad.division.pais.codigo_iso},
                'division': {'id': bodega.ciudad.division.geoname_id, 'nombre': bodega.ciudad.division.nombre, 'codigo': bodega.ciudad.division.codigo_iso},
                'ciudad': {'id': bodega.ciudad.geoname_id, 'nombre': bodega.ciudad.nombre}
            }
        return context

    def form_valid(self, form):
        messages.success(self.request, f'Bodega "{form.instance.nombre}" actualizada exitosamente.')
        return super().form_valid(form)


class BodegaDeleteView(EmpresaRequiredMixin, DeleteView):
    model = Bodega
    template_name = 'inventario/bodega_confirm_delete.html'
    success_url = reverse_lazy('inventario:lista_bodegas')

    def get_queryset(self):
        """
        Seguridad: Asegura que un usuario solo pueda eliminar bodegas de su empresa.
        """
        return Bodega.objects.filter(empresa=self.empresa_activa)


    def form_valid(self, form):
        bodega = self.get_object()
        bodega.activo = False
        bodega.save(update_fields=['activo'])
        messages.success(self.request, f'La bodega "{bodega.nombre}" ha sido eliminada.')
        return redirect(self.success_url)
