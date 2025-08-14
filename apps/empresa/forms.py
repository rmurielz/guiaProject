from django import forms
from django.core.cache import cache
from django.utils.translation import gettext_lazy as _
from .models import Empresa
from apps.terceros.models import TipoIdentificacion, Pais, Division, Ciudad # <-- IMPORT CORREGIDO
from apps.core.forms import UbicacionFormMixin

class EmpresaForm(UbicacionFormMixin, forms.ModelForm):
    """
    Formulario para la creación y edición de Empresas, con la capacidad
    de crear la ubicación geográfica sobre la marcha usando UbicacionFormMixin.
    """
    class Meta:
        model = Empresa
        # Limpiamos los campos para que coincidan con el modelo Empresa
        # El campo 'ciudad' se manejará a través del mixin.
        fields = ['nombre', 'tipo_identificacion', 'nif', 'email', 'direccion', 'telefono']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'nif': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'tipo_identificacion': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        tipos_identificacion = cache.get('tipos_identificacion_choices')
        if tipos_identificacion is None:
            tipos_identificacion = list(TipoIdentificacion.objects.all().order_by('nombre').values_list('id', 'nombre'))
            cache.set('tipos_identificacion_choices', tipos_identificacion, 3600)
        self.fields['tipo_identificacion'].choices = [('', '---------')] + tipos_identificacion

    def clean(self):
        cleaned_data = super().clean()
        if not self.instance.pk and not cleaned_data.get('ciudad_geoname_id'):
            raise forms.ValidationError(
                _("La selección de una ciudad es obligatoria para crear la empresa."),
                code='ciudad_requerida'
            )
        return cleaned_data

    def save(self, commit=True):
        """
        Integramos la lógica de guardado de ubicación del Mixin.
        """
        empresa_instance = super().save(commit=False)
        # Usamos el método del mixin para manejar la ubicación
        empresa_instance = self.save_ubicacion(empresa_instance)

        if commit:
            empresa_instance.save()
        return empresa_instance