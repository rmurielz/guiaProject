# C:/proyecto/Guia/terceros/admin.py
from django.contrib import admin
from django.db import models
from django.db.models import Count, Q
from .models import Tercero, TipoIdentificacion, TipoTercero, Pais, Division, Ciudad


@admin.register(Tercero)
class TerceroAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'nroid', 'tipo_tercero', 'ciudad_completa', 'telefono', 'email', 'activo')
    search_fields = ('nombre', 'nroid', 'nombre_comercial', 'email')
    list_filter = ('tipo_tercero', 'activo', 'ciudad__division__pais', 'tipo_identificacion')
    raw_id_fields = ('ciudad',)
    list_per_page = 20

    # Optimización crítica: precargamos todas las relaciones necesarias
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related(
            'tipo_identificacion',
            'tipo_tercero',
            'ciudad__division__pais'
        )

    def ciudad_completa(self, obj):
        """Muestra la ubicación completa sin queries adicionales."""
        if obj.ciudad:
            return f"{obj.ciudad.nombre}, {obj.ciudad.division.nombre}, {obj.ciudad.division.pais.nombre}"
        return "Sin ubicación"

    ciudad_completa.short_description = "Ubicación"

    # Agregar acciones masivas útiles
    actions = ['activar_terceros', 'desactivar_terceros']

    def activar_terceros(self, request, queryset):
        """Activa múltiples terceros de una vez."""
        updated = queryset.update(activo=True)
        self.message_user(request, f'{updated} terceros activados exitosamente.')

    activar_terceros.short_description = "Activar terceros seleccionados"

    def desactivar_terceros(self, request, queryset):
        """Desactiva múltiples terceros de una vez."""
        updated = queryset.update(activo=False)
        self.message_user(request, f'{updated} terceros desactivados exitosamente.')

    desactivar_terceros.short_description = "Desactivar terceros seleccionados"


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
    list_display = ('nombre', 'codigo_iso', 'geoname_id', 'total_terceros')
    search_fields = ('nombre', 'codigo_iso')
    list_per_page = 50

    def get_queryset(self, request):
        """Optimizamos con anotaciones para mostrar estadísticas."""
        queryset = super().get_queryset(request)
        return queryset.annotate(
            total_terceros_activos=Count('divisiones__ciudades__tercero', distinct=True)
        )

    def total_terceros(self, obj):
        """Muestra el total de terceros por país sin queries adicionales."""
        return obj.total_terceros_activos

    total_terceros.short_description = "Terceros Activos"
    total_terceros.admin_order_field = 'total_terceros_activos'


@admin.register(Division)
class DivisionAdmin(ReadOnlyAdmin):
    list_display = ('nombre', 'pais', 'codigo_iso', 'total_terceros')
    search_fields = ('nombre',)
    list_filter = ('pais',)
    list_per_page = 50

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('pais').annotate(
            total_terceros_activos=Count('ciudades__tercero', distinct=True)
        )

    def total_terceros(self, obj):
        return obj.total_terceros_activos

    total_terceros.short_description = "Terceros Activos"
    total_terceros.admin_order_field = 'total_terceros_activos'


@admin.register(Ciudad)
class CiudadAdmin(ReadOnlyAdmin):
    list_display = ('nombre', 'division_completa', 'total_terceros')
    search_fields = ('nombre',)
    list_filter = ('division__pais',)
    list_per_page = 50

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related(
            'division__pais'
        ).annotate(
            total_terceros_activos=Count('tercero', distinct=True)
        )

    def division_completa(self, obj):
        return f"{obj.division.nombre}, {obj.division.pais.nombre}"

    division_completa.short_description = "División/País"

    def total_terceros(self, obj):
        return obj.total_terceros_activos

    total_terceros.short_description = "Terceros Activos"
    total_terceros.admin_order_field = 'total_terceros_activos'


@admin.register(TipoTercero)
class TipoTerceroAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'total_terceros_activos')
    search_fields = ('nombre',)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(
            total_activos=Count('terceros', filter=Q(terceros__activo=True))
        )

    def total_terceros_activos(self, obj):
        return obj.total_activos

    total_terceros_activos.short_description = "Terceros Activos"
    total_terceros_activos.admin_order_field = 'total_activos'


@admin.register(TipoIdentificacion)
class TipoIdentificacionAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'total_terceros_activos')
    search_fields = ('nombre',)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(
            total_activos=Count('identificaciones', filter=Q(identificaciones__activo=True))
        )

    def total_terceros_activos(self, obj):
        return obj.total_activos

    total_terceros_activos.short_description = "Terceros Activos"
    total_terceros_activos.admin_order_field = 'total_activos'