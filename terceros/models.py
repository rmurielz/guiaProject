# C:/proyecto/Guia/terceros/models.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator

# --- Modelos Geográficos ---
# Esta estructura normalizada es preferible a usar campos de texto libre.

class Pais(models.Model):
    """Modelo para almacenar los países."""
    nombre = models.CharField(max_length=100, unique=True, verbose_name=_("Nombre"))
    codigo_iso = models.CharField(max_length=2, unique=True, verbose_name=_("Código ISO"))
    geoname_id = models.PositiveIntegerField(unique=True, null=True, blank=True, verbose_name=_("GeoNames ID"))

    class Meta:
        verbose_name = _("País")
        verbose_name_plural = _("Países")
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre

class Division(models.Model):
    """Modelo para almacenar divisiones/estados/departamentos de un país."""
    pais = models.ForeignKey(
        Pais, on_delete=models.CASCADE, related_name="divisiones", verbose_name=_("País")
    )
    nombre = models.CharField(max_length=100, verbose_name=_("Nombre"))
    codigo_iso = models.CharField(
        max_length=10, unique=True, verbose_name=_("Código ISO de subdivisión")
    )
    geoname_id = models.PositiveIntegerField(unique=True, null=True, blank=True, verbose_name=("GeoNames ID"))

    class Meta:
        verbose_name = _("División")
        verbose_name_plural = _("Divisiones")
        ordering = ["nombre"]
        # Asegura que no haya divisiones con el mismo nombre en el mismo país
        unique_together = (("pais", "nombre"),)

    def __str__(self):
        return f"{self.nombre}, {self.pais.nombre}"

class Ciudad(models.Model):
    """Modelo para almacenar las ciudades de una división."""
    division = models.ForeignKey(
        Division, on_delete=models.CASCADE, related_name="ciudades", verbose_name=_("División")
    )
    nombre = models.CharField(max_length=100, verbose_name=_("Nombre"))
    geoname_id = models.PositiveIntegerField(unique=True, null=True, blank=True, verbose_name=("GeoNames ID"))

    class Meta:
        verbose_name = _("Ciudad")
        verbose_name_plural = _("Ciudades")
        ordering = ["nombre"]
        # Asegura que no haya ciudades con el mismo nombre en la misma división
        unique_together = (("division", "nombre"),)

    def __str__(self):
        return f"{self.nombre}, {self.division.nombre}"


# --- Modelo Principal de Terceros (Actualizado) ---

class Tercero(models.Model):
    """
    Modelo para almacenar la información de terceros (clientes, proveedores, etc.).
    """

    # --- Opciones para los campos 'choices' (usando la clase TextChoices recomendada) ---
    class TipoTercero(models.TextChoices):
        CLIENTE = 'cliente', _('Cliente')
        PROVEEDOR = 'proveedor', _('Proveedor')
        EMPLEADO = 'empleado', _('Empleado')
        CONTRATISTA = 'contratista', _('Contratista')
        ENTIDAD_REGULATORIA = 'entidadregulatoria', _('Entidad Regulatoria')
        ENTIDAD_FINANCIERA = 'entidadfinanciera', _('Entidad Financiera')

    class TipoIdentificacion(models.TextChoices):
        CEDULA = 'cedula', _('Cédula de Ciudadanía')
        NIT = 'nit', _('NIT')
        RUC = 'ruc', _('RUC')
        TARJETA_IDENTIDAD = 'tarjetaidentidad', _('Tarjeta de Identidad')
        CEDULA_EXTRANJERIA = 'cedulaextranjeria', _('Cédula de Extranjería')
        PASAPORTE = 'pasaporte', _('Pasaporte')

    # --- Campos del Modelo ---

    # 1. Clasificación e Identificación
    tipo_tercero = models.CharField(
        max_length=20,
        choices=TipoTercero.choices,
        verbose_name=_('Tipo de Tercero')
    )
    tipo_identificacion = models.CharField(
        max_length=30,
        choices=TipoIdentificacion.choices,
        verbose_name=_('Tipo ID')
    )
    nroid = models.CharField(
        max_length=30,
        verbose_name=_('Número ID'),
        blank=False
    )
    digito_verificacion = models.PositiveIntegerField(
        verbose_name=_('DV'),
        blank=True,
        null=True,
        validators=[MinValueValidator(0), MaxValueValidator(9)],
#        help_text=_('Dígito de verificación si aplica.')
    )

    # 2. Nombres
    nombre = models.CharField(
        max_length=100,
        verbose_name=_('Nombre / Razón Social'),
        blank=False
    )
    nombre_comercial = models.CharField(
        max_length=50,
        verbose_name=_('Nombre Comercial'),
        blank=True
    )

    # 3. Localización (Refactorizado para usar ForeignKeys)
    ciudad = models.ForeignKey(
        Ciudad,
        on_delete=models.SET_NULL, # Si se borra una ciudad, no se borra el tercero
        null=True,
        blank=True,
        verbose_name=_("Ciudad")
    )
    direccion = models.CharField(
        max_length=100,
        verbose_name=_('Dirección'),
        blank=True
    )

    # 4. Contacto
    contacto = models.CharField(
        max_length=50,
        verbose_name=_('Nombre de Contacto'),
        blank=True
    )
    cargo = models.CharField(
        max_length=50,
        verbose_name=_('Cargo de Contacto'),
        blank=True
    )
    telefono = models.CharField(
        max_length=20,
        verbose_name=_('Teléfono'),
        blank=True
    )
    email = models.EmailField(
        max_length=100,
        verbose_name=_('Email'),
        blank=True,
        null=True
    )

    # 5. Metadatos de Auditoría
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Fecha de Creación')
    )
    fecha_modificacion = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Fecha de Modificación')
    )

    class Meta:
        verbose_name = _('Tercero')
        verbose_name_plural = _('Terceros')
        ordering = ['nombre']
        # Asegura que no se pueda registrar dos veces el mismo número de ID con el mismo tipo
        unique_together = (('tipo_identificacion', 'nroid'),)

    def __str__(self):
        """Representación en texto del objeto."""
        return f"{self.nombre} ({self.nroid})"

    def save(self, *args, **kwargs):
        """Sobrescribe el método save para normalizar datos antes de guardar."""
        # Capitaliza los campos de texto relevantes para un formato consistente
        fields_to_capitalize = [
            'nombre', 'nombre_comercial', 'direccion', 'contacto', 'cargo'
        ]
        for field_name in fields_to_capitalize:
            value = getattr(self, field_name)
            if isinstance(value, str):
                setattr(self, field_name, value.title())

        # Convierte el email a minúsculas
        if self.email:
            self.email = self.email.lower()

        super().save(*args, **kwargs)