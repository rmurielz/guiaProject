# C:/proyecto/Guia/terceros/views.py
import logging
import requests
from typing import List, Dict, Any, Optional
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.core.cache import cache
from apps.core.mixins import EmpresaRequiredMixin
from .forms import TerceroForm
from .models import Tercero, TipoTercero, TipoIdentificacion

# Obtenemos una instancia del logger para registrar eventos importantes, especialmente errores.
logger = logging.getLogger(__name__)


class TerceroListView(EmpresaRequiredMixin, ListView):
    model = Tercero
    template_name = 'terceros/tercero_list.html'
    context_object_name = 'terceros'
    paginate_by = 10

    def get_queryset(self):
        """
        Optimizado con select_related para evitar N+1 queries.
        Incluye la cadena completa de ubicación geográfica y filtra por estado.
        """
        base_queryset = Tercero.objects.filter(empresa=self.empresa_activa).select_related(
            'tipo_identificacion',
            'tipo_tercero',
            'ciudad__division__pais'  # Precarga toda la cadena geográfica
        )

        # Obtener el parámetro de estado, por defecto 'activos'
        estado = self.request.GET.get('estado', 'activos')

        if estado == 'activos':
            return base_queryset.filter(activo=True).order_by('nombre')
        elif estado == 'inactivos':
            return base_queryset.filter(activo=False).order_by('nombre')
        else: # 'todos' o cualquier otro valor
            return base_queryset.order_by('nombre')

    def get_context_data(self, **kwargs):
        """Añade el estado del filtro al contexto para usarlo en la plantilla."""
        context = super().get_context_data(**kwargs)
        context['estado_filtro'] = self.request.GET.get('estado', 'activos')
        return context

class TerceroCreateView(EmpresaRequiredMixin, PermissionRequiredMixin, CreateView):
    """
    Vista para crear un nuevo tercero, usando el patrón de Vistas Basadas en Clases.
    """
    model = Tercero
    form_class = TerceroForm
    template_name = 'terceros/tercero_form.html'
    success_url = reverse_lazy('terceros:Lista_terceros')
    permission_required = 'terceros.add_tercero'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Asegura que la variable siempre exista para el JS, especialmente en la creación
        context['ubicacion_inicial'] = None
        return context

    def form_valid(self, form):
        """
        Añadimos un mensaje de éxito antes de redirigir.
        """
        form.instance.empresa = self.empresa_activa
        messages.success(self.request, f'Tercero "{form.instance.nombre}" creado exitosamente.')
        return super().form_valid(form)


class TerceroUpdateView(EmpresaRequiredMixin, UpdateView):
    """
    Vista para editar un tercero existente - OPTIMIZADA
    """
    model = Tercero
    form_class = TerceroForm
    template_name = 'terceros/tercero_form.html'
    success_url = reverse_lazy('terceros:Lista_terceros')

    def get_queryset(self):
        """
        Seguridad: Asegura que un usuario solo pueda editar terceros
        de la empresa que tiene activa en su sesión.
        """
        return Tercero.objects.filter(empresa=self.empresa_activa)

    def get_context_data(self, **kwargs):
        """
        Optimizamos el contexto para evitar queries adicionales en el template.
        """
        context = super().get_context_data(**kwargs)

        # Si el tercero tiene ciudad, preparamos los datos para el frontend
        tercero = self.object
        # Aseguramos que la variable siempre exista, incluso si no hay ciudad
        context['ubicacion_inicial'] = None
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


class TerceroDeleteView(EmpresaRequiredMixin, DeleteView):
    """
    Vista para eliminar (suavemente) un tercero - OPTIMIZADA
    """
    model = Tercero
    template_name = 'terceros/tercero_confirm_delete.html'
    success_url = reverse_lazy('terceros:Lista_terceros')

    def get_queryset(self):
        """
        Seguridad: Asegura que un usuario solo pueda eliminar terceros de su empresa.
        """
        return Tercero.objects.filter(empresa=self.empresa_activa)

    def form_valid(self, form):
        """
        En lugar de borrar, implementamos la eliminación suave.
        """
        tercero = self.get_object()
        tercero.activo = False
        tercero.save(update_fields=['activo'])  # Optimización: solo actualiza el campo necesario
        messages.success(self.request, f'El tercero "{tercero.nombre}" ha sido eliminado.')
        return redirect(self.success_url)

class TerceroActivateView(EmpresaRequiredMixin, DeleteView):
    """
    Vista para reactivar un tercero que fue eliminado suavemente.
    Reutilizamos DeleteView por su simplicidad para manejar un POST a un objeto.
    """
    model = Tercero
    template_name = 'terceros/tercero_confirm_activate.html'
    success_url = reverse_lazy('terceros:Lista_terceros')

    def get_queryset(self):
        """
        Seguridad: Asegura que un usuario solo pueda activar terceros de su empresa.
        """
        return Tercero.objects.filter(empresa=self.empresa_activa)

    def form_valid(self, form):
        """
        En lugar de borrar, reactivamos el tercero.
        """
        tercero = self.get_object()
        tercero.activo = True
        tercero.save(update_fields=['activo'])
        messages.success(self.request, f'El tercero "{tercero.nombre}" ha sido reactivado exitosamente.')
        return redirect(self.success_url)

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


@login_required
def buscar_paises_geonames(request: HttpRequest) -> JsonResponse:
    """
    Búsqueda de países optimizada con cache y validación de datos.
    """
    username = settings.GEONAMES_USERNAME
    search_term = request.GET.get('q', '').lower()
    logger.debug(f"Buscando países con término: '{search_term}'")

    # Cache key único para la lista completa de países
    cache_key = f"geonames_paises_{username}"
    url = f"http://api.geonames.org/countryInfoJSON?username={username}&lang=es"

    cache_timeout = settings.CACHE_TIMEOUTS.get('GEONAMES_PAISES', 86400)
    data = _consultar_geonames_con_cache(url, cache_key, cache_timeout)

    paises = []
    for p in data:
        # Validación de datos: Asegurarse de que los campos necesarios existen
        if all(k in p for k in ['geonameId', 'countryName', 'countryCode']):
            paises.append({
                'id': p['geonameId'],
                'nombre': p['countryName'],
                'codigo': p['countryCode']
            })
        else:
            logger.warning(f"Dato de país incompleto recibido de GeoNames: {p}")

    # Filtrado local (más eficiente que múltiples requests a la API)
    if search_term:
        paises = [p for p in paises if search_term in p['nombre'].lower()]

    paises_ordenados = sorted(paises, key=lambda x: x['nombre'])

    results = paises_ordenados[:50] # Devolver hasta 50 para una mejor experiencia inicial
    logger.debug(f"Devolviendo {len(results)} países.")

    return JsonResponse(results, safe=False)


@login_required
def buscar_divisiones_geonames(request: HttpRequest) -> JsonResponse:
    """
    Búsqueda de divisiones optimizada con cache por país y validación de datos.
    """
    pais_geoname_id = request.GET.get('geoname_id')
    search_term = request.GET.get('q', '').lower()
    if not pais_geoname_id:
        return JsonResponse([], safe=False)

    logger.debug(f"Buscando divisiones para país {pais_geoname_id} con término: '{search_term}'")

    username = settings.GEONAMES_USERNAME
    cache_key = f"geonames_divisiones_{pais_geoname_id}_{username}"
    url = (f"http://api.geonames.org/childrenJSON?geonameId={pais_geoname_id}&username={username}&lang=es"
           f"&featureCode=ADM1&maxRows=500")

    cache_timeout = settings.CACHE_TIMEOUTS.get('GEONAMES_DIVISIONES', 21600)
    data = _consultar_geonames_con_cache(url, cache_key, cache_timeout)

    divisiones = []
    for d in data:
        if all(k in d for k in ['geonameId', 'name', 'adminCode1']):
            divisiones.append({
                'id': d['geonameId'],
                'nombre': d['name'],
                'codigo': d['adminCode1']
            })
        else:
            logger.warning(f"Dato de división incompleto recibido de GeoNames: {d}")

    if search_term:
        divisiones = [d for d in divisiones if search_term in d['nombre'].lower()]

    divisiones_ordenadas = sorted(divisiones, key=lambda x: x['nombre'])
    logger.debug(f"Devolviendo {len(divisiones_ordenadas)} divisiones.")
    return JsonResponse(divisiones_ordenadas, safe=False)


@login_required
def buscar_ciudades_geonames(request: HttpRequest) -> JsonResponse:
    """
    Búsqueda de ciudades optimizada con cache por división y validación de datos.
    """
    division_geoname_id = request.GET.get('geoname_id')
    search_term = request.GET.get('q', '').lower()
    if not division_geoname_id:
        return JsonResponse([], safe=False)

    logger.debug(f"Buscando ciudades para división {division_geoname_id} con término: '{search_term}'")

    username = settings.GEONAMES_USERNAME
    cache_key = f"geonames_ciudades_{division_geoname_id}_{username}"
    url = (f"http://api.geonames.org/childrenJSON?geonameId={division_geoname_id}&username={username}&lang=es"
           f"&featureCode=PPL&featureCode=PPLC&maxRows=1000")

    cache_timeout = settings.CACHE_TIMEOUTS.get('GEONAMES_CIUDADES', 7200)
    data = _consultar_geonames_con_cache(url, cache_key, cache_timeout)

    ciudades = []
    for c in data:
        if all(k in c for k in ['geonameId', 'name']):
            ciudades.append({'id': c['geonameId'], 'nombre': c['name']})
        else:
            logger.warning(f"Dato de ciudad incompleto recibido de GeoNames: {c}")

    if search_term:
        ciudades = [c for c in ciudades if search_term in c['nombre'].lower()]

    ciudades_ordenadas = sorted(ciudades, key=lambda x: x['nombre'])
    logger.debug(f"Devolviendo {len(ciudades_ordenadas)} ciudades.")
    return JsonResponse(ciudades_ordenadas, safe=False)


@login_required
def verificar_existencia_tercero(request: HttpRequest) -> JsonResponse:
    """
    Verifica si un tercero ya existe - Optimizada con select_related.
    """
    nro_id = request.GET.get('nroid')
    empresa_id = request.session.get('empresa_id')

    if not nro_id:
        return JsonResponse({'error': 'El número de identificación (nroid) es requerido.'}, status=400)

    if not empresa_id:
        # Esto no debería ocurrir si se llama desde la app, pero es una salvaguarda.
        return JsonResponse({'error': 'No hay una empresa activa en la sesión.'}, status=400)

    # Optimización: solo seleccionamos los campos necesarios
    tercero_existente = Tercero.objects.filter(
        empresa_id=empresa_id,
        nroid=nro_id.strip()
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