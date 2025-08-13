# C:/proyecto/Guia/terceros/urls.py
from django.urls import path
from . import views

app_name = 'terceros'

urlpatterns = [
    # URL para la vista de lista
    path('', views.TerceroListView.as_view(), name='Lista_terceros'),

    # URLs para el formulario de creación
    path('crear/', views.TerceroCreateView.as_view(), name='crear_tercero'),

    # URLs para editar y eliminar
    path('<int:pk>/editar/', views.TerceroUpdateView.as_view(), name='editar_tercero'),
    path('<int:pk>/eliminar/', views.TerceroDeleteView.as_view(), name='eliminar_tercero'),
    path('<int:pk>/activar/', views.TerceroActivateView.as_view(), name='activar_tercero'),

    # URLs para la API de GeoNames - OPTIMIZADAS CON CACHE
    # El cache se maneja dentro de las vistas para mayor control y eficiencia
    path('api/geonames/paises/', views.buscar_paises_geonames, name='api_buscar_paises'),
    path('api/geonames/divisiones/', views.buscar_divisiones_geonames, name='api_buscar_divisiones'),
    path('api/geonames/ciudades/', views.buscar_ciudades_geonames, name='api_buscar_ciudades'),

    # La verificación debe ser siempre en tiempo real, sin cache
    path('api/verificar-tercero/', views.verificar_existencia_tercero, name='api_verificar_tercero'),

    # URL utilitaria para administradores
    path('api/invalidar-cache/', views.invalidar_cache_geonames, name='api_invalidar_cache'),
]