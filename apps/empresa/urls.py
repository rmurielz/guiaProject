from django.urls import path
from . import views

app_name = 'empresa'

urlpatterns = [
    path('crear/', views.EmpresaCreateView.as_view(), name='crear_empresa'),
    path('seleccionar/', views.SeleccionarEmpresaView.as_view(), name='seleccionar_empresa'),
    # URL para la página de selección inicial después del login
    path('seleccionar-empresa/', views.SeleccionarEmpresaInicialView.as_view(), name='seleccionar_empresa_inicial'),
]