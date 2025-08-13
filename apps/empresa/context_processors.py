from .models import Empresa

def empresas_context(request):
    """
    Hace que la lista de empresas activas esté disponible en todas las plantillas
    para el selector de empresa.
    """
    if request.user.is_authenticated:
        # Seguridad: Devolvemos solo las empresas activas a las que el usuario tiene acceso.
        empresas = request.user.empresas.filter(activo=True).order_by('nombre')
        return {'empresas_disponibles': empresas}
    return {}