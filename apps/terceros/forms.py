from django import forms
from .models import Tercero, Pais, Division, Ciudad

class TerceroForm(forms.ModelForm):
    # Campos aidionales para recibir los datos de la ubicación desde el frontend.
    # No se guardan en el modelo Tercero directamente, por eso 'required=False'.
    pais_geoname_id = forms.IntegerField(required=False, widget=forms.HiddenInput())
    pais_nombre = forms.CharField(required=False, widget=forms.HiddenInput())
    pais_codigo_iso = forms.CharField(required=False, widget=forms.HiddenInput())

    division_geoname_id = forms.IntegerField(required=False, widget=forms.HiddenInput())
    division_nombre = forms.CharField(required=False, widget=forms.HiddenInput())
    division_codigo_iso = forms.CharField(required=False, widget=forms.HiddenInput())

    ciudad_geoname_id = forms.IntegerField(required=False, widget=forms.HiddenInput())
    ciudad_nombre = forms.CharField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = Tercero
        #Incluimos todos los campos del modelo que queremos en el formulario.
        #El campo ciudad 'ciudad' del modelo se asiganará anualmente en el metodo save.
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
        widgets={
            # Usamos 'form-control' para inputs de texto, número, email, etc.
            'nombre':forms.TextInput(attrs={'class':'form-control'}),
            'nombre_comercial':forms.TextInput(attrs={'class':'form-control'}),
            'nroid':forms.TextInput(attrs={'class':'form-control'}),
            'digito_verificacion':forms.NumberInput(attrs={'class':'form-control'}),
            'direccion':forms.TextInput(attrs={'class':'form-control'}),
            'contacto':forms.TextInput(attrs={'class':'form-control'}),
            'cargo':forms.TextInput(attrs={'class':'form-control'}),
            'telefono':forms.TextInput(attrs={'class':'form-control'}),
            'email':forms.EmailInput(attrs={'class':'form-control'}),

            # ¡Importante! Usamos 'form-select' para los campos de selección (desplegables)
            'tipo_tercero':forms.Select(attrs={'class':'form-select'}),
            'tipo_identificacion':forms.Select(attrs={'class':'form-select'}),
        }

    def clean_nroid(self):
        """
        Valida que el número de documento (nroid) sea único en toda la base de datos,
        independientemente del tipo de identificación.
        """
        # 1. Obtiene el dato limpio del campo del formulario
        nroid = self.cleaned_data.get('nroid')

        # 2. Si el campo no está vacío, procedemos a validar
        if nroid:
            # 3. Buscamos si ya existe un tercero con este número de documento.
            #    Usamos .exclude(pk=self.instance.pk) para que la validación
            #    funcione correctamente al EDITAR un tercero existente (ignora el propio objeto).
            if Tercero.objects.filter(nroid=nroid).exclude(pk=self.instance.pk).exists():
                # 4. Si existe, lanzamos un error de validación que Django mostrará.
                raise forms.ValidationError("Ya existe un tercero registrado con este número de documento.")

        # 5. Si todo está bien, devolvemos el dato limpio.
        return nroid

    def save(self, commit = True):
        """
        Sobreescribimos el metodo save para manejar la lógica de la ubicación.
        """
        #1.  Obtener o crear la ubicación
        ciudad = None
        ciudad_geoname_id = self.cleaned_data.get('ciudad_geoname_id')
        if ciudad_geoname_id:
            #Usamos get_or_create para evitar duplicados en la base de datos.
            pais, _= Pais.objects.update_or_create(
                codigo_iso=self.cleaned_data.get('pais_codigo_iso'),
                defaults={
                    'nombre':self.cleaned_data.get('pais_nombre'),
                    'geoname_id':self.cleaned_data.get('pais_geoname_id')
                }
            )
            division, _= Division.objects.update_or_create(
                codigo_iso=self.cleaned_data.get('division_codigo_iso'),
                defaults={
                    'nombre':self.cleaned_data.get('division_nombre'),
                    'geoname_id':self.cleaned_data.get('division_geoname_id'),
                    'pais':pais
                }
            )
            ciudad, _= Ciudad.objects.get_or_create(
                geoname_id=ciudad_geoname_id,
                defaults={
                    'nombre':self.cleaned_data.get('ciudad_nombre'),
                    'division':division
                }
            )
        # 2. Guardar la instancia del Tercero
        # Obtenemos la instancia del tercero, pero no la guardamos en la BD (commit=False)
        tercero_instance = super().save(commit=False)

        #Asignamos la ciudad que encontramos o creamos
        tercero_instance.ciudad = ciudad

        if commit:
            tercero_instance.save()
            #self.save_m2m() #Necesario si el formulario tuviera campos ManyToMany
        return tercero_instance
