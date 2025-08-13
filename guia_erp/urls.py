"""
URL configuration for ERP project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from apps.core import views as core_views


urlpatterns = [
    path('', core_views.landing_page_view, name='landing_page'),
    path('dashboard/', core_views.dashboard_view, name='dashboard'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('terceros/', include('apps.terceros.urls', namespace='terceros')),
    path('inventario/', include('apps.inventario.urls', namespace='inventario')),
    path('empresas/', include('apps.empresa.urls', namespace='empresa')),
    path('usuarios/', include('apps.usuarios.urls', namespace='usuarios')),
    path('admin/', admin.site.urls),
]