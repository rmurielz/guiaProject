from django.urls import path
from . import views

app_name = 'empresa'

urlpatterns = [
    # URL para la vista de creación de empresas
    path('crear/', views.EmpresaCreateView.as_view(), name='crear_empresa'),
    # URL para la acción de seleccionar una empresa (ahora usa POST)
    path('seleccionar/', views.SeleccionarEmpresaView.as_view(), name='seleccionar_empresa'),
]