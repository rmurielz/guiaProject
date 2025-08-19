import logging
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages

logger = logging.getLogger(__name__)

class EmpresaSeleccionadaMiddleware:
    """
    Middleware que gestiona la selección de empresa para el usuario.

    - Si un usuario tiene una sola empresa, la selecciona automáticamente.
    - Si tiene varias, lo redirige a una página de selección si no ha elegido una.
    - Adjunta la empresa activa (`empresa_activa`) al objeto `request`.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Ignorar superusuarios (que operan a nivel global) y usuarios no autenticados.
        if not request.user.is_authenticated or request.user.is_superuser:
            return self.get_response(request)

        # Definir rutas que NUNCA requieren una empresa seleccionada.
        # Es crucial que la página de selección y la acción de seleccionar estén aquí.
        allowed_paths = [
            reverse('empresa:seleccionar_empresa_inicial'),
            reverse('empresa:seleccionar_empresa'), # La acción POST que guarda la selección
            reverse('logout'),
            reverse('empresa:crear_empresa'), # Permitir crear la primera empresa
        ]

        # Si ya hay una empresa en la sesión, la adjuntamos al request y continuamos.
        # Esta es la ruta más común y eficiente.
        if 'empresa_id' in request.session:
            # Adjuntamos el objeto empresa para fácil acceso en las vistas
            request.empresa_activa = request.user.empresas.filter(
                pk=request.session.get('empresa_id')
            ).first()
            return self.get_response(request)

        # Si no hay empresa en sesión y el usuario intenta acceder a una página protegida...
        if not request.path.startswith('/admin/') and request.path not in allowed_paths:
            empresas_usuario = request.user.empresas.filter(activo=True)
            num_empresas = empresas_usuario.count()

            if num_empresas == 1:
                # Caso 1: Auto-seleccionar si solo tiene una empresa.
                empresa = empresas_usuario.first()
                request.session['empresa_id'] = empresa.id
                request.session['empresa_nombre'] = empresa.nombre
                request.empresa_activa = empresa # Adjuntamos para la petición actual
                messages.info(request, f"Empresa '{empresa.nombre}' seleccionada automáticamente.")
                # No redirigimos, dejamos que la petición original continúe ya con la sesión configurada.

            elif num_empresas > 1:
                # Caso 2: Redirigir a la página de selección si tiene varias.
                return redirect('empresa:seleccionar_empresa_inicial')

            # Caso 3 (num_empresas == 0): No hacemos nada. La vista (ej. dashboard)
            # se encargará de mostrar el mensaje de "No tienes empresas asignadas".

        return self.get_response(request)