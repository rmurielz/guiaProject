from django.urls import path
from . import views

app_name = 'inventario'

urlpatterns = [
    # URLs para el CRUD de Bodegas
    path('bodegas/', views.BodegaListView.as_view(), name='lista_bodegas'),
    path('bodegas/crear/', views.BodegaCreateView.as_view(), name='crear_bodega'),
    path('bodegas/<int:pk>/editar/', views.BodegaUpdateView.as_view(), name='editar_bodega'),
    path('bodegas/<int:pk>/eliminar/', views.BodegaDeleteView.as_view(), name='eliminar_bodega'),

    # Aquí añadiremos más URLs para productos, movimientos, etc.
]