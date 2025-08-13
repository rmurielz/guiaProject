from django.contrib import admin
from .models import Bodega


@admin.register(Bodega)
class BodegaAdmin(admin.ModelAdmin):
    """Configuración del modelo Bodega en el panel de administración."""
    list_display = ('nombre', 'ciudad', 'responsable', 'activo', 'fecha_creacion')
    list_filter = ('activo', 'ciudad__division__pais', 'ciudad')
    search_fields = ('nombre', 'direccion', 'responsable__nombre')
    list_per_page = 20
