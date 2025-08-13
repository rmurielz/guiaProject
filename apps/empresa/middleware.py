import logging
from django.shortcuts import redirect
from django.urls import reverse

logger = logging.getLogger(__name__)

class EmpresaSeleccionadaMiddleware:
    """
    Middleware que verifica si el usuario ha seleccionado una empresa.
    Si no lo ha hecho, lo redirige a una página de selección.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Rutas que no requieren una empresa seleccionada
        # Usamos startswith para que sea más robusto
        exempt_urls = [
            reverse('login'),
            reverse('logout'),
            reverse('dashboard'),
            reverse('empresa:crear_empresa'), # Permitir crear la primera empresa
            '/admin/',
            '/empresas/seleccionar/',
            '/terceros/api/geonames/',
        ]

        is_exempt = any(request.path.startswith(url) for url in exempt_urls)

        # --- INICIO DE DEBUG ---
        # Imprime cada ruta que el middleware está evaluando.
        logger.info(f"[DEBUG MIDDLEWARE] Path: '{request.path}' | Exempt: {is_exempt} | User: {request.user} | Empresa ID: {request.session.get('empresa_id')}")
        # --- FIN DE DEBUG ---

        # Permitir acceso al admin sin empresa seleccionada
        if request.path.startswith('/admin/'):
            return self.get_response(request)

        # Si el usuario está autenticado y no ha seleccionado empresa
        if request.user.is_authenticated and not request.session.get('empresa_id'):
            # Y no está intentando acceder a una ruta exenta
            if not any(request.path.startswith(url) for url in exempt_urls):
                # Y hay empresas disponibles para seleccionar
                from .models import Empresa
                if Empresa.objects.filter(activo=True).exists():
                    return redirect('dashboard') # Redirigir al dashboard donde puede seleccionar

        return self.get_response(request)