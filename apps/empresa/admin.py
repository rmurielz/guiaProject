from django.contrib import admin
from .models import Empresa

# Register your models here.
@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    """
    Configuración del modelo Empresa en el panel de administración de Django
    """
    list_display = ('nombre', 'tipo_identificacion', 'nif', 'ciudad', 'activo', 'fecha_creacion')
    list_filter = ('activo', 'ciudad__division__pais')
    search_fields = ('nombre', 'nif', 'email')
    list_per_page = 20
    ordering = ('nombre',)