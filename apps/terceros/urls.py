# C:/proyecto/Guia/terceros/views.py
from django.urls import path
from . import views

app_name = 'terceros'

urlpatterns = [
    #URL para la  vista de lita
    path('', views.TerceroListView.as_view(), name='Lista_terceros'),

    # --- URL para el formulario de creación ---
    path('crear/',views.tercero_create_view, name='crear_tercero'),
    # URls para editar y eliminar -----
    path('<int:pk>/editar/', views.TerceroUpdateView.as_view(), name='editar_tercero'),
    path('<int:pk>/eliminar/', views.TerceroDeleteView.as_view(), name='eliminar_tercero'),

    # URLs para la API de GeoNames
    path('api/geonames/paises/', views.buscar_paises_geonames, name='api_buscar_paises'),
    path('api/geonames/divisiones/', views.buscar_divisiones_geonames, name='api_buscar_divisiones'),
    path('api/geonames/ciudades/', views.buscar_ciudades_geonames, name='api_buscar_ciudades'),
    path('api/verificar-tercero/', views.verificar_existencia_tercero, name='api_verificar_tercero')
]
