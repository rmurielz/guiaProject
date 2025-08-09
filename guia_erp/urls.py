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
from apps.terceros import views as terceros_views


urlpatterns = [
    path('', terceros_views.dashboard_view, name='dashboard'),
    path('info/', terceros_views.landing_page_view, name='landing_page'),
    path('terceros/', include('apps.terceros.urls', namespace='terceros')),
    path('admin/', admin.site.urls),
]