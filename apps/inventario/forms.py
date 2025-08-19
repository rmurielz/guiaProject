from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Bodega
from apps.terceros.models import Tercero
from apps.core.forms import UbicacionFormMixin


class BodegaForm(UbicacionFormMixin, forms.ModelForm):
    """
    Formulario para la creación y edición de Bodegas, utilizando el mixin
    de ubicación para una lógica centralizada y limpia.
    """
    class Meta:
        model = Bodega
        fields = ['nombre', 'direccion', 'responsable']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'responsable': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        # Extraemos la empresa antes de llamar al padre para usarla en las validaciones
        self.empresa = kwargs.pop('empresa', None)
        super().__init__(*args, **kwargs)

        # Filtrar el queryset de responsables para mostrar solo los de la empresa activa.
        if self.empresa:
            self.fields['responsable'].queryset = Tercero.objects.filter(
                activo=True, empresa=self.empresa
            ).order_by('nombre')
        else:
            self.fields['responsable'].queryset = Tercero.objects.none()

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
        # Solo validamos en la creación, no en la edición
        if not self.instance.pk and not cleaned_data.get('ciudad_geoname_id'):
            raise forms.ValidationError(
                _("La selección de una ciudad es obligatoria para la bodega."),
                code='ciudad_requerida'
            )
        return cleaned_data

    def save(self, commit=True):
        bodega_instance = super().save(commit=False)
        bodega_instance.empresa = self.empresa # Asignamos la empresa activa
        bodega_instance = self.save_ubicacion(bodega_instance)
        if commit:
            bodega_instance.save()
        return bodega_instance