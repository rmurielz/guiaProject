from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from apps.core.models import TimeStampedModel, SoftDeleteModel

class Empresa(TimeStampedModel, SoftDeleteModel):
    """
    Representa una de las empresas del grupo empresarial.
    Este es el modelo central para la arquitectura multi-empresa.
    """
    nombre = models.CharField(_('Nombre o Razón Social'), max_length=255, unique=True)
    tipo_identificacion = models.ForeignKey(
        'terceros.TipoIdentificacion',
        on_delete=models.PROTECT,
        verbose_name=_('Tipo de Identificación')
    )
    nif = models.CharField(_('NIF / NIT / RUT'), max_length=20, unique=True)
    ciudad = models.ForeignKey(
        'terceros.Ciudad',
        on_delete=models.PROTECT,
        verbose_name=_('Ciudad (Domicilio Fiscal)')
    )
    direccion = models.CharField(_('Dirección'), max_length=255, blank=True)
    telefono = models.CharField(_('Teléfono'), max_length=50, blank=True)
    email = models.EmailField(_('Email'), blank=True)
    usuarios = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='empresas',
        blank=True,
        verbose_name=_('Usuarios con Acceso')
    )

    class Meta:
        verbose_name = _('Empresa')
        verbose_name_plural = _('Empresas')
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        """
        Sobrescribe el método save para normalizar datos clave
        antes de guardarlos en la base de datos.
        """
        # Capitaliza los campos de texto relevantes para un formato consistente
        self.nombre = self.nombre.title()
        if self.direccion:
            self.direccion = self.direccion.title()

        # Convierte el email a minúsculas para consistencia
        if self.email:
            self.email = self.email.lower()

        super().save(*args, **kwargs)