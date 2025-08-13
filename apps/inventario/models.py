from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import TimeStampedModel, SoftDeleteModel
from apps.terceros.models import Ciudad, Tercero


class Bodega(TimeStampedModel, SoftDeleteModel):
    """
    Representa una ubicación física (almacén, sucursal, etc.)
    donde se almacena el inventario.
    """
    empresa = models.ForeignKey(
        'empresa.Empresa',
        on_delete=models.PROTECT,
        related_name='bodegas',
        verbose_name=_('Empresa Propietaria')
    )
    nombre = models.CharField(
        _('Nombre de la Bodega'),
        max_length=100,
        help_text=_('Ej: Bodega Principal, Sucursal Norte, Almacén Central')
    )
    ciudad = models.ForeignKey(
        Ciudad,
        on_delete=models.PROTECT,
        related_name='bodegas',
        verbose_name=_('Ciudad'),
        help_text=_('Ubicación geográfica de la bodega.')
    )
    direccion = models.CharField(
        _('Dirección'),
        max_length=255,
        blank=True,
        null=True,
        help_text=_('Dirección física detallada de la bodega.')
    )
    responsable = models.ForeignKey(
        Tercero,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bodegas_a_cargo',
        verbose_name=_('Responsable'),
        help_text=_('Tercero responsable de la gestión de la bodega.')
    )

    class Meta:
        verbose_name = _('Bodega')
        verbose_name_plural = _('Bodegas')
        ordering = ['nombre']
        unique_together = ('empresa', 'nombre')

    def __str__(self):
        return self.nombre
