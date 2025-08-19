from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

class Perfil(models.Model):
    """
    Extiende el modelo de Usuario de Django para añadir campos específicos
    de la aplicación, como el rol de administrador de empresa.
    """
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='perfil')
    es_admin_empresa = models.BooleanField(
        _('Administrador de Empresa'),
        default=False,
        help_text=_('Designa a este usuario como administrador de las empresas a las que está asignado.')
    )

    def __str__(self):
        return f"Perfil de {self.usuario.username}"

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def crear_o_actualizar_perfil_usuario(sender, instance, created, **kwargs):
    """Crea un perfil automáticamente cuando se crea un nuevo usuario."""
    if created:
        Perfil.objects.create(usuario=instance)
    instance.perfil.save()
