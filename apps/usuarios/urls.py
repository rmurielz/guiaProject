from django.urls import path
from . import views

app_name = 'usuarios'

urlpatterns = [
    path('crear-global/', views.UserCreateView.as_view(), name='crear_usuario_global'),
    path('crear/', views.EmpresaUserCreateView.as_view(), name='crear_usuario_empresa'),
]