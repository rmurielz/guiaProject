from django.urls import path
from . import views

app_name = 'usuarios'

urlpatterns = [
    path('crear/', views.UserCreateView.as_view(), name='crear_usuario'),
]