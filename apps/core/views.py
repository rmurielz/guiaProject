from django.shortcuts import render
from django.http import HttpRequest, HttpResponse
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.db.models import Count, Q
from django.utils import timezone
from django.conf import settings

from apps.terceros.models import Tercero, TipoTercero


@login_required
def dashboard_view(request: HttpRequest) -> HttpResponse:
    """
    Vista para la página de inicio/dashboard del ERP.
    Muestra estadísticas filtradas por la empresa seleccionada.
    """
    empresa_id = request.session.get('empresa_id')

    if not empresa_id:
        return render(request, 'terceros/dashboard.html', {'stats': None})

    try:
        # Validamos que el ID de la sesión sea un entero válido
        empresa_pk = int(empresa_id)
    except (ValueError, TypeError):
        # Si no es válido, lo tratamos como si no hubiera empresa seleccionada
        return render(request, 'terceros/dashboard.html', {'stats': None})

    cache_key = f'dashboard_stats_{empresa_pk}'
    stats = cache.get(cache_key)

    if stats is None:
        terceros_empresa = Tercero.objects.filter(empresa_id=empresa_pk)

        terceros_stats = terceros_empresa.aggregate(
            total_activos=Count('id', filter=Q(activo=True)),
            total_inactivos=Count('id', filter=Q(activo=False)),
            total_general=Count('id')
        )

        top_tipos = TipoTercero.objects.annotate(
            total_terceros=Count('terceros', filter=Q(terceros__activo=True, terceros__empresa_id=empresa_pk))
        ).filter(total_terceros__gt=0).order_by('-total_terceros')[:5]

        top_paises = terceros_empresa.filter(
            activo=True,
            ciudad__isnull=False
        ).values(
            'ciudad__division__pais__nombre'
        ).annotate(
            total=Count('id')
        ).order_by('-total')[:5]

        stats = {
            'terceros': terceros_stats,
            'top_tipos': list(top_tipos.values('nombre', 'total_terceros')),
            'top_paises': list(top_paises),
            'ultima_actualizacion': timezone.now()
        }
        cache.set(cache_key, stats, settings.CACHE_TIMEOUTS['DASHBOARD_STATS'])

    context = {'stats': stats}
    return render(request, 'terceros/dashboard.html', context)


def landing_page_view(request: HttpRequest) -> HttpResponse:
    """Vista para la página de aterrizaje pública."""
    return render(request, 'terceros/landing_page.html')