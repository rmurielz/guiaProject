# C:/proyecto/Guia/terceros/views.py
import logging
import requests
from typing import List, Dict, Any
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.csrf import ensure_csrf_cookie
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.core.cache import cache
from django.db.models import Count, Q
from .forms import TerceroForm
from .models import Tercero, TipoTercero, TipoIdentificacion

# Obtenemos una instancia del logger para registrar eventos importantes, especialmente errores.
logger = logging.getLogger(__name__)


class TerceroListView(ListView):
    model = Tercero
    template_name = 'terceros/tercero_list.html'
    context_object_name = 'terceros'
    paginate_by = 10

    def get_queryset(self):
        """
        Optimizado con select_related para evitar N+1 queries.
        Incluye la cadena completa de ubicación geográfica.
        """
        return Tercero.objects.select_related(
            'tipo_identificacion',
            'tipo_tercero',
            'ciudad__division__pais'  # Precarga toda la cadena geográfica
        ).filter(activo=True).order_by('nombre')

class TerceroCreateView(CreateView):
    """
    Vista para crear un nuevo tercero, usando el patrón de Vistas Basadas en Clases.
    """
    model = Tercero
    form_class = TerceroForm
    template_name = 'terceros/tercero_form.html'
    success_url = reverse_lazy('terceros:Lista_terceros')

    def form_valid(self, form):
        """
        Añadimos un mensaje de éxito antes de redirigir.
        """
        messages.success(self.request, f'Tercero "{form.instance.nombre}" creado exitosamente.')
        return super().form_valid(form)


class TerceroUpdateView(UpdateView):
    """
    Vista para editar un tercero existente - OPTIMIZADA
    """
    model = Tercero
    form_class = TerceroForm
    template_name = 'terceros/tercero_form.html'
    success_url = reverse_lazy('terceros:Lista_terceros')

    def get_object(self, queryset=None):
        """
        Sobrescribimos get_object para optimizar la carga del tercero a editar.
        Precargamos todas las relaciones necesarias.
        """
        if queryset is None:
            queryset = self.get_queryset()

        # Optimización crítica: precargamos todas las relaciones
        queryset = queryset.select_related(
            'tipo_identificacion',
            'tipo_tercero',
            'ciudad__division__pais'
        )

        pk = self.kwargs.get(self.pk_url_kwarg)
        if pk is not None:
            return get_object_or_404(queryset, pk=pk)

        raise AttributeError("TerceroUpdateView debe llamarse con un object pk.")

    def get_context_data(self, **kwargs):
        """
        Optimizamos el contexto para evitar queries adicionales en el template.
        """
        context = super().get_context_data(**kwargs)

        # Si el tercero tiene ciudad, preparamos los datos para el frontend
        tercero = self.object
        if tercero.ciudad:
            context['ubicacion_inicial'] = {
                'pais': {
                    'id': tercero.ciudad.division.pais.geoname_id,
                    'nombre': tercero.ciudad.division.pais.nombre,
                    'codigo': tercero.ciudad.division.pais.codigo_iso
                },
                'division': {
                    'id': tercero.ciudad.division.geoname_id,
                    'nombre': tercero.ciudad.division.nombre,
                    'codigo': tercero.ciudad.division.codigo_iso
                },
                'ciudad': {
                    'id': tercero.ciudad.geoname_id,
                    'nombre': tercero.ciudad.nombre
                }
            }

        return context

    def form_valid(self, form):
        """
        Añadimos un mensaje de éxito antes de redirigir
        """
        messages.success(self.request, f'Tercero "{form.instance.nombre}" actualizado exitosamente.')
        return super().form_valid(form)


class TerceroDeleteView(DeleteView):
    """
    Vista para eliminar (suavemente) un tercero - OPTIMIZADA
    """
    model = Tercero
    template_name = 'terceros/tercero_confirm_delete.html'
    success_url = reverse_lazy('terceros:Lista_terceros')

    def get_object(self, queryset=None):
        """
        Optimizamos la carga del objeto para eliminación.
        """
        if queryset is None:
            queryset = self.get_queryset()

        # Solo necesitamos los datos básicos para mostrar en la confirmación
        queryset = queryset.select_related('tipo_identificacion')

        pk = self.kwargs.get(self.pk_url_kwarg)
        return get_object_or_404(queryset, pk=pk)

    def form_valid(self, form):
        """
        En lugar de borrar, implementamos la eliminación suave.
        """
        tercero = self.get_object()
        tercero.activo = False
        tercero.save(update_fields=['activo'])  # Optimización: solo actualiza el campo necesario
        messages.success(self.request, f'El tercero "{tercero.nombre}" ha sido eliminado.')
        return redirect(self.success_url)


def dashboard_view(request: HttpRequest) -> HttpResponse:
    """
    Vista optimizada para la página de inicio/dashboard del ERP.
    Muestra estadísticas útiles con queries eficientes.
    """
    # Cache de 5 minutos para las estadísticas del dashboard
    cache_key = 'dashboard_stats'
    stats = cache.get(cache_key)

    if stats is None:
        # Query optimizada que calcula múltiples métricas en una sola consulta
        terceros_stats = Tercero.objects.aggregate(
            total_activos=Count('id', filter=Q(activo=True)),
            total_inactivos=Count('id', filter=Q(activo=False)),
            total_general=Count('id')
        )

        # Top 5 tipos de terceros más utilizados
        top_tipos = TipoTercero.objects.annotate(
            total_terceros=Count('terceros', filter=Q(terceros__activo=True))
        ).filter(total_terceros__gt=0).order_by('-total_terceros')[:5]

        # Estadísticas geográficas (países con más terceros)
        top_paises = Tercero.objects.filter(
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

        # Cache por 5 minutos
        cache.set(cache_key, stats, 300)

    context = {
        'stats': stats,
    }
    return render(request, 'terceros/dashboard.html', context)


def landing_page_view(request: HttpRequest) -> HttpResponse:
    return render(request, 'terceros/landing_page.html')


def _consultar_geonames_con_cache(url: str, cache_key: str, cache_time: int = 3600) -> List[Dict[str, Any]]:
    """
    Función auxiliar optimizada con cache para consultar la API de GeoNames.
    Los datos geográficos cambian raramente, por lo que el cache es muy efectivo.
    """
    # Intentar obtener desde cache primero
    cached_data = cache.get(cache_key)
    if cached_data is not None:
        logger.debug(f"Cache hit para: {cache_key}")
        return cached_data

    # Si no está en cache, consultar API
    logger.debug(f"Cache miss para: {cache_key}, consultando API...")

    try:
        response = requests.get(url, timeout=10)

        # Manejar explícitamente el límite de peticiones (Rate Limit)
        if response.status_code == 429:
            logger.warning("Límite de peticiones a la API de GeoNames excedido. URL: %s", url)
            return []

        # Lanza una excepción para otros códigos de error (4xx/5xx)
        response.raise_for_status()

        data = response.json().get('geonames', [])

        # Guardar en cache solo si obtuvimos datos válidos
        if data:
            cache.set(cache_key, data, cache_time)
            logger.debug(f"Datos guardados en cache: {cache_key}")

        return data

    except requests.Timeout:
        logger.error("Timeout al intentar conectar con la API de GeoNames. URL: %s", url)
    except requests.RequestException as e:
        logger.error("Error de red o HTTP al consultar GeoNames: %s. URL: %s", e, url)

    # En caso de cualquier error, devolvemos una lista vacía para que el frontend no falle.
    return []


def buscar_paises_geonames(request: HttpRequest) -> JsonResponse:
    """
    Búsqueda de países optimizada con cache.
    Los países cambian raramente, cache de 24 horas.
    """
    username = settings.GEONAMES_USERNAME
    search_term = request.GET.get('q', '').lower()

    # Cache key único para la lista completa de países
    cache_key = f"geonames_paises_{username}"
    url = f"http://api.geonames.org/countryInfoJSON?username={username}&lang=es"

    # Cache de 24 horas para países (cambian muy raramente)
    data = _consultar_geonames_con_cache(url, cache_key, 86400)

    paises = [
        {'id': p['geonameId'], 'nombre': p['countryName'], 'codigo': p['countryCode']}
        for p in data
    ]

    # Filtrado local (más eficiente que múltiples requests a la API)
    if search_term:
        paises = [p for p in paises if search_term in p['nombre'].lower()]

    paises_ordenados = sorted(paises, key=lambda x: x['nombre'])
    return JsonResponse(paises_ordenados[:20], safe=False)


def buscar_divisiones_geonames(request: HttpRequest) -> JsonResponse:
    """
    Búsqueda de divisiones optimizada con cache por país.
    """
    pais_geoname_id = request.GET.get('geoname_id')
    search_term = request.GET.get('q', '').lower()
    if not pais_geoname_id:
        return JsonResponse([], safe=False)

    username = settings.GEONAMES_USERNAME

    # Cache key específico por país
    cache_key = f"geonames_divisiones_{pais_geoname_id}_{username}"
    url = (f"http://api.geonames.org/childrenJSON?geonameId={pais_geoname_id}&username={username}&lang=es"
           f"&featureCode=ADM1&maxRows=500")

    # Cache de 6 horas para divisiones
    data = _consultar_geonames_con_cache(url, cache_key, 21600)

    divisiones = [
        {'id': d['geonameId'], 'nombre': d['name'], 'codigo': d['adminCode1']}
        for d in data
    ]

    # Filtrado local por término de búsqueda
    if search_term:
        divisiones = [d for d in divisiones if search_term in d['nombre'].lower()]

    divisiones_ordenadas = sorted(divisiones, key=lambda x: x['nombre'])
    return JsonResponse(divisiones_ordenadas, safe=False)


def buscar_ciudades_geonames(request: HttpRequest) -> JsonResponse:
    """
    Búsqueda de ciudades optimizada con cache por división.
    """
    division_geoname_id = request.GET.get('geoname_id')
    search_term = request.GET.get('q', '').lower()
    if not division_geoname_id:
        return JsonResponse([], safe=False)

    username = settings.GEONAMES_USERNAME

    # Cache key específico por división
    cache_key = f"geonames_ciudades_{division_geoname_id}_{username}"
    url = (f"http://api.geonames.org/childrenJSON?geonameId={division_geoname_id}&username={username}&lang=es"
           f"&featureCode=PPL&featureCode=PPLC&maxRows=1000")

    # Cache de 2 horas para ciudades (pueden cambiar con más frecuencia)
    data = _consultar_geonames_con_cache(url, cache_key, 7200)

    ciudades = [
        {'id': c['geonameId'], 'nombre': c['name']}
        for c in data
    ]

    # Filtrado local por término de búsqueda
    if search_term:
        ciudades = [c for c in ciudades if search_term in c['nombre'].lower()]

    ciudades_ordenadas = sorted(ciudades, key=lambda x: x['nombre'])
    return JsonResponse(ciudades_ordenadas, safe=False)


def verificar_existencia_tercero(request: HttpRequest) -> JsonResponse:
    """
    Verifica si un tercero ya existe - Optimizada con select_related.
    """
    nro_id = request.GET.get('nroid')

    if not nro_id:
        return JsonResponse({'error': 'El número de identificación (nroid) es requerido.'}, status=400)

    # Optimización: solo seleccionamos los campos necesarios
    tercero_existente = Tercero.objects.filter(
        nroid=nro_id
    ).only('nombre', 'nroid').first()

    if tercero_existente:
        return JsonResponse({
            'existe': True,
            'nombre': tercero_existente.nombre
        })
    else:
        return JsonResponse({'existe': False})


def invalidar_cache_geonames(request: HttpRequest) -> JsonResponse:
    """
    Vista utilitaria para invalidar el cache de GeoNames (útil para desarrollo/administración).
    """
    if not request.user.is_staff:
        return JsonResponse({'error': 'No autorizado'}, status=403)

    cache_pattern = 'geonames_*'
    # En producción con Redis, usarías cache.delete_pattern()
    # Para desarrollo, limpiamos manualmente las keys conocidas
    cache_keys = [
        f"geonames_paises_{settings.GEONAMES_USERNAME}",
        'dashboard_stats'
    ]

    cache.delete_many(cache_keys)

    return JsonResponse({
        'mensaje': 'Cache de GeoNames invalidado exitosamente',
        'keys_eliminadas': cache_keys
    })


# Import necesario para timezone que se usa en dashboard_view
from django.utils import timezone