# C:/proyecto/Guia/terceros/admin.py
from django.contrib import admin
from .models import Tercero, TipoIdentificacion, TipoTercero, Pais, Division, Ciudad


@admin.register(Tercero)
class TerceroAdmin(admin.ModelAdmin):
    list_display = ('id','nombre', 'nroid', 'tipo_tercero', 'ciudad', 'telefono', 'email')
    search_fields = ('nombre', 'nroid', 'nombre_comercial', 'ciudad__nombre')
    list_filter = ('tipo_tercero', 'ciudad__division__pais')
    raw_id_fields = ('ciudad',)  # Mejora el rendimiento para muchas ciudades


class ReadOnlyAdmin(admin.ModelAdmin):
    """Clase base para hacer un modelo de solo lectura en el admin."""
    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(Pais)
class PaisAdmin(ReadOnlyAdmin):
    list_display = ('nombre', 'codigo_iso','geoname_id')
    search_fields = ('nombre', 'codigo_iso')

@admin.register(Division)
class DivisionAdmin(ReadOnlyAdmin):
    list_display = ('nombre', 'pais', 'codigo_iso')
    search_fields = ('nombre',)
    list_filter = ('pais',)

@admin.register(Ciudad)
class CiudadAdmin(ReadOnlyAdmin):
    list_display = ('nombre', 'division')
    search_fields = ('nombre',)
    list_filter = ('division__pais',)

@admin.register(TipoTercero)
class TipoTerceroAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)

@admin.register(TipoIdentificacion)
class TipoIdentificacionAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)