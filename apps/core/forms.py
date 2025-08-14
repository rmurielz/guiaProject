from django import forms
from django.db import transaction
from apps.terceros.models import Pais, Division, Ciudad

class UbicacionFormMixin(forms.Form):
    """
    Un Mixin reutilizable que proporciona los campos y la lógica de guardado
    para la información de ubicación geográfica obtenida de GeoNames.
    """
    # 1. Campos ocultos que el frontend (location-selector.js) llenará.
    pais_geoname_id = forms.IntegerField(required=False, widget=forms.HiddenInput())
    pais_nombre = forms.CharField(required=False, widget=forms.HiddenInput())
    pais_codigo_iso = forms.CharField(required=False, widget=forms.HiddenInput())

    division_geoname_id = forms.IntegerField(required=False, widget=forms.HiddenInput())
    division_nombre = forms.CharField(required=False, widget=forms.HiddenInput())
    division_codigo_iso = forms.CharField(required=False, widget=forms.HiddenInput())

    ciudad_geoname_id = forms.IntegerField(required=False, widget=forms.HiddenInput())
    ciudad_nombre = forms.CharField(required=False, widget=forms.HiddenInput())

    def save_ubicacion(self, instance):
        """
        Procesa los datos de ubicación del formulario y los asocia a una
        instancia de modelo (ej. Empresa o Tercero).
        Esta función debe ser llamada desde el método save() del formulario principal.
        """
        ciudad_geoname_id = self.cleaned_data.get('ciudad_geoname_id')

        if ciudad_geoname_id:
            # Usamos transaction.atomic para asegurar la integridad de los datos.
            with transaction.atomic():
                pais, _ = Pais.objects.update_or_create(
                    codigo_iso=self.cleaned_data.get('pais_codigo_iso'),
                    defaults={
                        'nombre': self.cleaned_data.get('pais_nombre'),
                        'geoname_id': self.cleaned_data.get('pais_geoname_id')
                    }
                )
                division, _ = Division.objects.update_or_create(
                    codigo_iso=self.cleaned_data.get('division_codigo_iso'),
                    defaults={
                        'nombre': self.cleaned_data.get('division_nombre'),
                        'geoname_id': self.cleaned_data.get('division_geoname_id'),
                        'pais': pais
                    }
                )
                ciudad, _ = Ciudad.objects.get_or_create(
                    geoname_id=ciudad_geoname_id,
                    defaults={'nombre': self.cleaned_data.get('ciudad_nombre'), 'division': division}
                )
                instance.ciudad = ciudad
        return instance