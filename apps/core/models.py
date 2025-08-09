from django.db import models
from django.utils.translation import gettext_lazy as _

class TimeStampedModel(models.Model):
    """
    Modelo abstracto que proporciona campos de auditoría
    para todas las entidades del sistema.
    """
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Fecha de Creación')
    )
    fecha_modificacion = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Fecha de Modificación')
    )

    class Meta:
        abstract = True

class SoftDeleteModel(models.Model):
    """
    Modelo abstracto para implementar eliminación suave (soft delete)
    """
    activo = models.BooleanField(default=True, verbose_name=_('Activo'))

    class Meta:
        abstract = True
