# C:/proyecto/Guia/terceros/admin.py
from django.contrib import admin
from .models import Tercero, Pais, Division, Ciudad


@admin.register(Tercero)
class TerceroAdmin(admin.ModelAdmin):
    list_display = ('id','nombre', 'nroid', 'tipo_tercero', 'ciudad', 'telefono', 'email')
    search_fields = ('nombre', 'nroid', 'nombre_comercial', 'ciudad__nombre')
    list_filter = ('tipo_tercero', 'ciudad__division__pais')
    raw_id_fields = ('ciudad',)  # Mejora el rendimiento para muchas ciudades


@admin.register(Pais)
class PaisAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'codigo_iso')
    search_fields = ('nombre', 'codigo_iso')


@admin.register(Division)
class DivisionAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'pais', 'codigo_iso')
    search_fields = ('nombre', 'codigo_iso')
    list_filter = ('pais',)


@admin.register(Ciudad)
class CiudadAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'division')
    search_fields = ('nombre',)
    list_filter = ('division__pais', 'division')
    raw_id_fields = ('division',)
