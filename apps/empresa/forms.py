from django import forms
from django.db import transaction
from django.core.cache import cache
from django.utils.translation import gettext_lazy as _
from .models import Empresa
from apps.terceros.models import Pais, Division, Ciudad, TipoIdentificacion


class EmpresaForm(forms.ModelForm):
    """
    Formulario para la creación y edición de Empresas, con la capacidad
    de crear la ubicación geográfica sobre la marcha.
    """
    # Campos ocultos para la ubicación
    pais_geoname_id = forms.IntegerField(required=False, widget=forms.HiddenInput())
    pais_nombre = forms.CharField(required=False, widget=forms.HiddenInput())
    pais_codigo_iso = forms.CharField(required=False, widget=forms.HiddenInput())

    division_geoname_id = forms.IntegerField(required=False, widget=forms.HiddenInput())
    division_nombre = forms.CharField(required=False, widget=forms.HiddenInput())
    division_codigo_iso = forms.CharField(required=False, widget=forms.HiddenInput())

    ciudad_geoname_id = forms.IntegerField(required=False, widget=forms.HiddenInput())
    ciudad_nombre = forms.CharField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = Empresa
        fields = ['nombre', 'tipo_identificacion', 'nif', 'direccion', 'telefono', 'email']
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
        # Optimización: Reutilizamos el cache de tipos de identificación que ya usa TerceroForm
        tipos_identificacion = cache.get('tipos_identificacion_choices')
        if tipos_identificacion is None:
            tipos_identificacion = list(TipoIdentificacion.objects.all().order_by('nombre').values_list('id', 'nombre'))
            cache.set('tipos_identificacion_choices', tipos_identificacion, 3600)

        # Aplicar las opciones cacheadas
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
        with transaction.atomic():
            ciudad_geoname_id = self.cleaned_data.get('ciudad_geoname_id')
            if ciudad_geoname_id:
                pais, _ = Pais.objects.update_or_create(
                    codigo_iso=self.cleaned_data.get('pais_codigo_iso'),
                    defaults={'nombre': self.cleaned_data.get('pais_nombre'), 'geoname_id': self.cleaned_data.get('pais_geoname_id')}
                )
                division, _ = Division.objects.update_or_create(
                    codigo_iso=self.cleaned_data.get('division_codigo_iso'),
                    defaults={'nombre': self.cleaned_data.get('division_nombre'), 'geoname_id': self.cleaned_data.get('division_geoname_id'), 'pais': pais}
                )
                ciudad, _ = Ciudad.objects.get_or_create(
                    geoname_id=ciudad_geoname_id,
                    defaults={'nombre': self.cleaned_data.get('ciudad_nombre'), 'division': division}
                )
                self.instance.ciudad = ciudad

            empresa_instance = super().save(commit=False)
            if commit:
                empresa_instance.save()
            return empresa_instance