# C:/proyecto/Guia/terceros/models.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.core.models import TimeStampedModel, SoftDeleteModel

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

class TipoTercero(models.Model):
    nombre = models.CharField(max_length=50, unique=True,verbose_name=("Tipo de tercero"))

    class Meta:
        verbose_name = _("Tipo de Tercero")
        verbose_name_plural = _("Tipos de Tercero")
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre

class TipoIdentificacion(models.Model):
    nombre = models.CharField(max_length=50, unique=True,verbose_name=("Nombre"))

    class Meta:
        verbose_name = _("Tipo de ID")
        verbose_name_plural = _("Tipos de ID")
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre

class Tercero(TimeStampedModel, SoftDeleteModel):
    """
    Modelo para almacenar la información de terceros (clientes, proveedores, etc.).
    """

    # --- Campos del Modelo ---
    empresa = models.ForeignKey(
        'empresa.Empresa',
        on_delete=models.PROTECT,
        related_name='terceros',
        verbose_name=_('Empresa')
    )

    # 1. Clasificación e Identificación
    tipo_tercero = models.ForeignKey(
        TipoTercero,
        on_delete=models.PROTECT,
        related_name='terceros',
        blank=False,
        verbose_name=_('Tipo de Tercero')
    )

    tipo_identificacion = models.ForeignKey(
        TipoIdentificacion,
        on_delete=models.PROTECT,
        related_name='identificaciones',
        blank=False,
        verbose_name=_('Tipo ID')
    )
    nroid = models.CharField(
        max_length=30,
        # La unicidad se define en `unique_together` para que sea por empresa
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

    class Meta:
        verbose_name = _('Tercero')
        verbose_name_plural = _('Terceros')
        ordering = ['nombre']
        unique_together = ('empresa', 'nroid')

    def __str__(self):
        """Representación en texto del objeto."""
        return f"{self.nombre} ({self.nroid})"

    def save(self, *args, **kwargs):
        """Sobrescribe el método save para normalizar datos antes de guardar."""
        # Normaliza campos de texto a formato Título y quita espacios extra.
        for field_name in ['nombre', 'nombre_comercial', 'direccion', 'contacto', 'cargo']:
            value = getattr(self, field_name, None)
            if value:
                setattr(self, field_name, value.strip().title())

        # Convierte el email a minúsculas y quita espacios
        if self.email:
            self.email = self.email.lower().strip()

        # Normaliza el NIF/ID quitando espacios
        if self.nroid:
            self.nroid = self.nroid.strip()

        super().save(*args, **kwargs)