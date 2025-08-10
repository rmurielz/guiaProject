# C:/proyecto/Guia/terceros/views.py
import logging
import requests
from typing import List, Dict, Any
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.conf import settings
from django.core.cache import cache
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.csrf import ensure_csrf_cookie
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, UpdateView, DeleteView
from .forms import TerceroForm
from .models import Tercero

# Obtenemos una instancia del logger para registrar eventos importantes, especialmente errores.
logger = logging.getLogger(__name__)

class TerceroListView(ListView):
    model = Tercero
    template_name = 'terceros/tercero_list.html' # Plantilla que creamos a contiinuación
    context_object_name = 'terceros' # Nombre que daremos a la plantilla
    paginate_by = 10

    def get_queryset(self):
        """
        Sobreescribimos para ordenar los resultados y, en el futuro,
        podríamos añadir filtros de búsqueda aquí.
        """
        return Tercero.objects.filter(activo=True).order_by('nombre')

class TerceroUpdateView(UpdateView):
    """
    Vista para editar un tercero existente
    """
    model = Tercero
    form_class = TerceroForm
    template_name = 'terceros/tercero_form.html'
    success_url = reverse_lazy('terceros:Lista_terceros')

    def form_valid(self, form):
        """
        Añadimos un mensaje de éxito antes de redirigir
        """
        messages.success(self.request, f'Tercero "{form.instance.nombre}" actualizado exitosamente.')
        return super().form_valid(form)

class TerceroDeleteView(DeleteView):
    """
    Vista para eliminar (suavemente) un tercero
    """
    model = Tercero
    template_name = 'terceros/tercero_confirm_delete.html'
    success_url = reverse_lazy('terceros:Lista_terceros')

    def form_valid(self, form):
        """
        En lugar de borrar, implementamos la eliminación suave.
        """
        tercero = self.get_object()
        tercero.activo = False
        tercero.save()
        messages.success(self.request, f'El tercero "{tercero.nombre}" ha sido eliminado.')
        return redirect(self.success_url)

def dashboard_view(request: HttpRequest) -> HttpResponse:
    """
    Vista para la página de inicio/dashboard del ERP.
    Muestra estadísticas y accesos directos.
    """
    total_terceros = Tercero.objects.count()
    context = {
        'total_terceros': total_terceros,
    }
    return render(request, 'terceros/dashboard.html')


def landing_page_view(request: HttpRequest) -> HttpResponse:
    return render(request, 'terceros/landing_page.html')


def _consultar_geonames(url: str) -> List[Dict[str, Any]]:
    """
    Función auxiliar centralizada para consultar la API de GeoNames.
    Maneja timeouts, rate limits, y otros errores de red de forma robusta.
    """
    # 1. Crear una clave única para la caché basada en la URL
    cache_key = f"geonames_query_{hash(url)}"

    # 2. Intentar obtener los datos de la caché
    cached_data = cache.get(cache_key)
    if cached_data is not None:
        logger.info("Respuesta de GeoNames obtenida desde la caché para la URL: %s", url)
        return cached_data

    logger.info("Realizando petición a la API de GeoNames (no en caché): %s", url)
    try:
        response = requests.get(url, timeout=10)

        # Manejar explícitamente el límite de peticiones (Rate Limit)
        if response.status_code == 429:
            logger.warning("Límite de peticiones a la API de GeoNames excedido. URL: %s", url)
            # No devolvemos error al cliente, sino una lista vacía para no romper el frontend.
            return []

        # Lanza una excepción para otros códigos de error (4xx/5xx)
        response.raise_for_status()

        data = response.json().get('geonames', [])

        # 3. Guardar la respuesta exitosa en la caché por 1 semana (604800 segundos)
        cache.set(cache_key, data, timeout=604800)

        return data

    except requests.Timeout:
        logger.error("Timeout al intentar conectar con la API de GeoNames. URL: %s", url)
    except requests.RequestException as e:
        logger.error("Error de red o HTTP al consultar GeoNames: %s. URL: %s", e, url)

    # En caso de cualquier error, devolvemos una lista vacía para que el frontend no falle.
    return []


def buscar_paises_geonames(request: HttpRequest) -> JsonResponse:
    username = settings.GEONAMES_USERNAME
    search_term = request.GET.get('q', '').lower()
    url = f"http://api.geonames.org/countryInfoJSON?username={username}&lang=es"

    data = _consultar_geonames(url)
    paises = [
        {'id': p['geonameId'], 'nombre': p['countryName'], 'codigo': p['countryCode']}
        for p in data
    ]

    # El endpoint de países no permite filtrar por nombre en la API, así que lo hacemos aquí.
    if search_term:
        paises = [p for p in paises if search_term in p['nombre'].lower()]

    paises_ordenados = sorted(paises, key=lambda x: x['nombre'])
    return JsonResponse(paises_ordenados[:20], safe=False)


def buscar_divisiones_geonames(request: HttpRequest) -> JsonResponse:
    pais_geoname_id = request.GET.get('geoname_id')
    search_term = request.GET.get('q', '').lower()
    if not pais_geoname_id:
        return JsonResponse([], safe=False)

    username = settings.GEONAMES_USERNAME
    # Se trae la lista completa de divisiones. El filtrado por búsqueda se hará en Python
    # para permitir búsquedas de subcadenas (ej: "bogota" en "Distrito Capital de Bogotá").
    # Esta es la lógica correcta que prioriza la funcionalidad sobre una optimización fallida.
    url = (f"http://api.geonames.org/childrenJSON?geonameId={pais_geoname_id}&username={username}&lang=es"
           f"&featureCode=ADM1&maxRows=500")

    data = _consultar_geonames(url)
    divisiones = [
        {'id': d['geonameId'], 'nombre': d['name'], 'codigo': d['adminCode1']}
        for d in data
    ]

    # Se filtra la lista en Python si el usuario ha introducido un término de búsqueda.
    if search_term:
        divisiones = [d for d in divisiones if search_term in d['nombre'].lower()]

    divisiones_ordenadas = sorted(divisiones, key=lambda x: x['nombre'])
    return JsonResponse(divisiones_ordenadas, safe=False)


def buscar_ciudades_geonames(request: HttpRequest) -> JsonResponse:
    division_geoname_id = request.GET.get('geoname_id')
    search_term = request.GET.get('q', '').lower()
    if not division_geoname_id:
        return JsonResponse([], safe=False)

    username = settings.GEONAMES_USERNAME
    # Se trae la lista completa de ciudades. Se incluyen PPL (lugar poblado) y PPLC (capital)
    # para asegurar que casos como Bogotá (PPLC) se listen correctamente.
    url = (f"http://api.geonames.org/childrenJSON?geonameId={division_geoname_id}&username={username}&lang=es"
           f"&featureCode=PPL&featureCode=PPLC&maxRows=1000")

    data = _consultar_geonames(url)
    ciudades = [
        {'id': c['geonameId'], 'nombre': c['name']}
        for c in data
    ]

    # Se filtra la lista en Python si el usuario ha introducido un término de búsqueda.
    if search_term:
        ciudades = [c for c in ciudades if search_term in c['nombre'].lower()]

    ciudades_ordenadas = sorted(ciudades, key=lambda x: x['nombre'])
    return JsonResponse(ciudades_ordenadas, safe=False)

@ensure_csrf_cookie
def tercero_create_view(request: HttpRequest) -> HttpResponse:
    if request.method == 'POST':
        form = TerceroForm(request.POST)
        if form.is_valid():
            tercero = form.save()
            messages.success(request, f'Tercero "{tercero.nombre}" creado exitosamente')
            return redirect(reverse('terceros:crear_tercero'))
        else:
            messages.error(request,'Error en creación de tercero, verifique la información ingresada')
    else:
        form = TerceroForm()

    # Nota: Para el versionado de estáticos, una solución más robusta a futuro
    # es usar ManifestStaticFilesStorage de Django, que lo hace automáticamente.
    context = {
        'form': form,
        'CSS_VERSION': '1.0.1', # Incrementa este número cuando cambies main.css
        'JS_VERSION': '1.0.2',  # Incrementa este número cuando cambies el JS
    }
    return render(request, 'terceros/tercero_form.html', context)


def verificar_existencia_tercero(request: HttpRequest) -> JsonResponse:
    """
    Verifica si un tercero ya existe en la base de datos basado ÚNICAMENTE en el número de identificación.
    Es una vista para ser consumida por AJAX/Fetch desde el frontend.
    """
    # El tipo de identificación ya no es necesario para esta validación.
    # tipo_id = request.GET.get('tipo_identificacion')
    nro_id = request.GET.get('nroid')

    if not nro_id:
        return JsonResponse({'error': 'El número de identificación (nroid) es requerido.'}, status=400)

    # La consulta ahora solo filtra por el número de documento.
    tercero_existente = Tercero.objects.filter(nroid=nro_id).first()

    if tercero_existente:
        return JsonResponse({
            'existe': True,
            'nombre': tercero_existente.nombre
        })
    else:
        return JsonResponse({'existe': False})
