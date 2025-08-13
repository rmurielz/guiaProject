from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import Tercero, TipoIdentificacion, TipoTercero


@receiver([post_save, post_delete], sender=Tercero)
def invalidar_cache_dashboard(sender, instance, **kwargs):
    """
    Invalida el cache del dashboard de una empresa específica cuando un tercero
    de esa empresa se crea, actualiza o elimina.
    """
    if instance.empresa_id:
        cache_key = f"dashboard_stats_{instance.empresa_id}"
        cache.delete(cache_key)

@receiver([post_save, post_delete], sender=TipoIdentificacion)
def invalidar_cache_tipos_id(sender, instance, **kwargs):
    """Invalida el cache de los tipos de identificación cuando cambian."""
    cache.delete('tipos_identificacion_choices')

@receiver([post_save, post_delete], sender=TipoTercero)
def invalidar_cache_tipos_tercero(sender, instance, **kwargs):
    """Invalida el cache de los tipos de tercero cuando cambian."""
    cache.delete('tipos_tercero_choices')