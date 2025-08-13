from django.contrib import messages
from django.shortcuts import redirect
from apps.empresa.models import Empresa

class EmpresaRequiredMixin:
    """
    Un mixin que verifica que una empresa esté seleccionada en la sesión.
    Si no, redirige al dashboard con un mensaje de error.
    Hace que self.empresa_activa esté disponible en la vista.
    """
    def dispatch(self, request, *args, **kwargs):
        empresa_id = request.session.get('empresa_id')
        if not empresa_id:
            messages.error(request, "Por favor, seleccione una empresa para continuar.")
            return redirect('dashboard')

        try:
            # Validamos que el ID sea un entero y que la empresa exista y esté activa.
            empresa_pk = int(empresa_id)
            self.empresa_activa = Empresa.objects.get(pk=empresa_pk, activo=True)
        except (ValueError, TypeError, Empresa.DoesNotExist):
            # Si el ID no es válido o la empresa no existe, limpiamos la sesión.
            request.session.pop('empresa_id', None)
            request.session.pop('empresa_nombre', None)
            messages.error(request, "La empresa seleccionada no es válida. Por favor, elija otra.")
            return redirect('dashboard')

        return super().dispatch(request, *args, **kwargs)