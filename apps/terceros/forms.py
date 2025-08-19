# C:/proyecto/Guia/terceros/forms.py
from django import forms
from django.conf import settings
from django.core.cache import cache
from .models import Tercero, TipoTercero, TipoIdentificacion
from apps.core.forms import UbicacionFormMixin


class TerceroForm(UbicacionFormMixin, forms.ModelForm):
    class Meta:
        model = Tercero
        fields = [
            'tipo_tercero',
            'tipo_identificacion',
            'nroid',
            'digito_verificacion',
            'nombre',
            'nombre_comercial',
            'direccion',
            'contacto',
            'cargo',
            'telefono',
            'email',
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre_comercial': forms.TextInput(attrs={'class': 'form-control'}),
            'nroid': forms.TextInput(attrs={'class': 'form-control'}),
            'digito_verificacion': forms.NumberInput(attrs={'class': 'form-control'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'contacto': forms.TextInput(attrs={'class': 'form-control'}),
            'cargo': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'tipo_tercero': forms.Select(attrs={'class': 'form-select'}),
            'tipo_identificacion': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        """
        Optimización crítica: precargamos las opciones de los selectores
        para evitar queries N+1 cuando se renderizan múltiples formularios
        o cuando el formulario se muestra varias veces.
        """
        # Extraemos la empresa antes de llamar al padre para usarla en las validaciones
        self.empresa = kwargs.pop('empresa', None)
        super().__init__(*args, **kwargs)

        # Cache de 1 hora para los tipos (cambian raramente)
        tipos_tercero = cache.get('tipos_tercero_choices')
        if tipos_tercero is None:
            tipos_tercero = list(TipoTercero.objects.all().order_by('nombre').values_list('id', 'nombre'))
            cache.set('tipos_tercero_choices', tipos_tercero, settings.CACHE_TIMEOUTS['FORM_CHOICES'])

        tipos_identificacion = cache.get('tipos_identificacion_choices')
        if tipos_identificacion is None:
            tipos_identificacion = list(TipoIdentificacion.objects.all().order_by('nombre').values_list('id', 'nombre'))
            cache.set('tipos_identificacion_choices', tipos_identificacion, settings.CACHE_TIMEOUTS['FORM_CHOICES'])

        # Aplicar las opciones cacheadas
        self.fields['tipo_tercero'].choices = [('', '---------')] + tipos_tercero
        self.fields['tipo_identificacion'].choices = [('', '---------')] + tipos_identificacion

    def clean_nroid(self):
        """
        Valida que el número de documento (nroid) sea único,
        optimizada para evitar queries innecesarias.
        """
        nroid = self.cleaned_data.get('nroid')

        if nroid and self.empresa:
            # Optimización: usamos only() para traer solo el campo que necesitamos validar
            query = Tercero.objects.filter(empresa=self.empresa, nroid=nroid)

            # Si estamos editando, excluimos el propio objeto de la validación
            if self.instance and self.instance.pk:
                query = query.exclude(pk=self.instance.pk)
            # Solo verificamos la existencia, no necesitamos todos los campos
            if query.only('id').exists():
                raise forms.ValidationError("Ya existe un tercero registrado con este número de documento.")

        return nroid

    def save(self, commit=True):
        """
        Sobrescribimos save para integrar la lógica de guardado de ubicación del Mixin.
        """
        # Primero, guardamos la instancia del Tercero sin commit para obtener un objeto.
        tercero_instance = super().save(commit=False)

        # Usamos el metodo del mixin para manejar la ubicación
        tercero_instance = self.save_ubicacion(tercero_instance)

        if commit:
            # El metodo save() del modelo se encargará de la normalización de campos
            tercero_instance.save()
        return tercero_instance