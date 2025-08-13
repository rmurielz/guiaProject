from django import forms
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from .models import Bodega
from apps.terceros.models import Pais, Division, Ciudad, Tercero


class BodegaForm(forms.ModelForm):
    """
    Formulario para la creación y edición de Bodegas, con la capacidad
    de crear la ubicación geográfica sobre la marcha.
    """
    # Campos ocultos para recibir los datos de la ubicación desde el frontend.
    pais_geoname_id = forms.IntegerField(required=False, widget=forms.HiddenInput())
    pais_nombre = forms.CharField(required=False, widget=forms.HiddenInput())
    pais_codigo_iso = forms.CharField(required=False, widget=forms.HiddenInput())

    division_geoname_id = forms.IntegerField(required=False, widget=forms.HiddenInput())
    division_nombre = forms.CharField(required=False, widget=forms.HiddenInput())
    division_codigo_iso = forms.CharField(required=False, widget=forms.HiddenInput())

    ciudad_geoname_id = forms.IntegerField(required=False, widget=forms.HiddenInput())
    ciudad_nombre = forms.CharField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = Bodega
        fields = ['nombre', 'direccion', 'responsable']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'responsable': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, empresa_id=None, **kwargs):
        super().__init__(*args, **kwargs)

        # Filtrar el queryset de responsables para mostrar solo los de la empresa activa.
        if empresa_id:
            self.fields['responsable'].queryset = Tercero.objects.filter(
                activo=True, empresa_id=empresa_id
            ).order_by('nombre')
        else:
            self.fields['responsable'].queryset = Tercero.objects.none()

        self.fields['responsable'].required = False

    def clean_nombre(self):
        """
        Normaliza el nombre de la bodega a formato de título (mayúsculas iniciales).
        """
        nombre = self.cleaned_data.get('nombre')
        if nombre:
            return nombre.strip().title()
        return nombre

    def clean_direccion(self):
        """
        Normaliza la dirección a formato de título (mayúsculas iniciales).
        """
        direccion = self.cleaned_data.get('direccion')
        if direccion:
            return direccion.strip().title()
        return direccion

    def clean(self):
        """Validación para asegurar que se ha seleccionado una ciudad."""
        cleaned_data = super().clean()
        if not cleaned_data.get('ciudad_geoname_id'):
            raise forms.ValidationError(
                _("La selección de una ciudad es obligatoria para la bodega."),
                code='ciudad_requerida'
            )
        return cleaned_data

    def save(self, commit=True):
        """
        Guarda la instancia de la Bodega, creando la ubicación si es necesario.
        """
        with transaction.atomic():
            # 1. Obtener o crear la ubicación geográfica
            pais, _ = Pais.objects.update_or_create(
                codigo_iso=self.cleaned_data.get('pais_codigo_iso'),
                defaults={'nombre': self.cleaned_data.get('pais_nombre'), 'geoname_id': self.cleaned_data.get('pais_geoname_id')}
            )
            division, _ = Division.objects.update_or_create(
                codigo_iso=self.cleaned_data.get('division_codigo_iso'),
                defaults={'nombre': self.cleaned_data.get('division_nombre'), 'geoname_id': self.cleaned_data.get('division_geoname_id'), 'pais': pais}
            )
            ciudad, _ = Ciudad.objects.get_or_create(
                geoname_id=self.cleaned_data.get('ciudad_geoname_id'),
                defaults={'nombre': self.cleaned_data.get('ciudad_nombre'), 'division': division}
            )

            # 2. Asignar la ciudad y guardar la Bodega
            bodega_instance = super().save(commit=False)
            bodega_instance.ciudad = ciudad
            if commit:
                bodega_instance.save()
            return bodega_instance