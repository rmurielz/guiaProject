# C:/proyecto/Guia/terceros/views.py
from django.urls import path
from . import views

app_name = 'terceros'

urlpatterns = [

    # --- URL para el formulario de creación ---
    path('crear/',views.tercero_create_view, name='crear_tercero'),
    # URLs para la API de GeoNames
    path('api/geonames/paises/', views.buscar_paises_geonames, name='api_buscar_paises'),
    path('api/geonames/divisiones/', views.buscar_divisiones_geonames, name='api_buscar_divisiones'),
    path('api/geonames/ciudades/', views.buscar_ciudades_geonames, name='api_buscar_ciudades'),
    path('api/verificar-tercero/', views.verificar_existencia_tercero, name='api_verificar_tercero')
]
