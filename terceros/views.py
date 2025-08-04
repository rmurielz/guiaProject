# C:/proyecto/Guia/terceros/views.py
from re import search

import requests
from django.http import JsonResponse
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.csrf import ensure_csrf_cookie
from django.urls import reverse
from .forms import TerceroForm
from .models import Tercero

def dashboard_view(request):
    """
    Vista para la página de inicio/dashboard del ERP.
    Muestra estadísticas y accesos directos.
    """
    total_terceros = Tercero.objects.count()
    context = {
        'total_terceros': total_terceros,
    }
    return render(request, 'terceros/dashboard.html')

def landing_page_view(request):
    return render(request, 'terceros/landing_page.html')

# Vista para buscar países en GeoNames
def buscar_paises_geonames(request):
    username = settings.GEONAMES_USERNAME
    search_term = request.GET.get('q', '').lower()
    url = f"http://api.geonames.org/countryInfoJSON?username={username}&lang=es"

    try:
        response = requests.get(url)
        response.raise_for_status()  # Lanza un error para respuestas 4xx/5xx
        data = response.json().get('geonames', [])
        # Formateamos los datos para nuestro frontend
        paises = [
            {'id': p['geonameId'], 'nombre': p['countryName'], 'codigo': p['countryCode']}
            for p in data
        ]
        if search_term:
            paises = [p for p in paises if search_term in p['nombre'].lower()]

        paises_ordenados = sorted(paises, key=lambda x: x['nombre'])
        return JsonResponse(paises_ordenados[:20], safe=False)
    except requests.RequestException as e:
        return JsonResponse({'error': str(e)}, status=500)

# Vista para buscar divisiones (estados/departamentos) de un país
def buscar_divisiones_geonames(request):
    pais_geoname_id = request.GET.get('geoname_id')
    search_term = request.GET.get('q', '').lower()
    if not pais_geoname_id:
        return JsonResponse([], safe=False)

    username = settings.GEONAMES_USERNAME
    # Usamos featureCode=ADM1 para obtener divisiones administrativas de primer nivel
    url = f"http://api.geonames.org/childrenJSON?geonameId={pais_geoname_id}&username={username}&lang=es&featureCode=ADM1"

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json().get('geonames', [])
        divisiones = [
            {'id': d['geonameId'], 'nombre': d['name'], 'codigo': d['adminCode1']}
            for d in data
        ]

        if search_term:
            divisiones = [d for d in divisiones if search_term in d['nombre'].lower()]

        divisiones_ordenadas = sorted(divisiones, key=lambda x: x['nombre'])
        return JsonResponse(divisiones_ordenadas, safe=False)
    except requests.RequestException as e:
        return JsonResponse({'error': str(e)}, status=500)

# Vista para buscar ciudades de una división
def buscar_ciudades_geonames(request):
    division_geoname_id = request.GET.get('geoname_id')
    search_term = request.GET.get('q', '').lower()
    if not division_geoname_id:
        return JsonResponse([], safe=False)

    username = settings.GEONAMES_USERNAME
    # PPL son lugares poblados (ciudades, pueblos, etc.)
    url = f"http://api.geonames.org/childrenJSON?geonameId={division_geoname_id}&username={username}&lang=es&featureCode=PPL"

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json().get('geonames', [])
        ciudades = [
            {'id': c['geonameId'], 'nombre': c['name']}
            for c in data
        ]

        if search_term:
            ciudades = [c for c in ciudades if search_term in c['nombre'].lower()]

        ciudades_ordenadas = sorted(ciudades, key=lambda x: x['nombre'])
        return JsonResponse(ciudades_ordenadas, safe=False)
    except requests.RequestException as e:
        return JsonResponse({'error': str(e)}, status=500)

@ensure_csrf_cookie
def tercero_create_view(request):
    if request.method == 'POST':
        # Pasamos todos los datos del POST al formulario.
        # El formulario ahora sabe cómo manejar los campos de ubicación.
        form = TerceroForm(request.POST)
        if form.is_valid():
            tercero = form.save() # ¡toda la lógica de guardado está encapsulada en el formulario!
            messages.success(request, f'Tercero "{tercero.nombre}" creado exitosamente')
            return redirect(reverse('terceros:crear_tercero'))
        else:
            messages.error(request,'Error en creación de tercero, verifique la información ingresada')
    else:
        # Si es un GET, simplemente creamos un formulario vacío.
        form = TerceroForm()

    # Aquí definimos las versiones y las pasamos al contexto
    context = {
        'form': form,
        'CSS_VERSION': '1.0.1', # Incrementa este número cuando cambies main.css
        'JS_VERSION': '1.0.2',  # Incrementa este número cuando cambies el JS
    }
    return render(request, 'terceros/tercero_form.html', context)

def verificar_existencia_tercero(request):
    """
    Verifica si un tercero ya existe en la base de datos basado en el tipo y número de identificación
    Es una vista para ser consumida por AJAX/Fetch desde el frontend.
    """
    tipo_id = request.GET.get('tipo_identificacion')
    nro_id = request.GET.get('nroid')

    # Validamos que los parámetros necesarios estén presentes
    if not tipo_id or not nro_id:
        return JsonResponse({'error': 'Tipo ID y Nro ID son requeridos.'}, status=400)
    # Usamos .first() para obtener el objeto si existe.  Es eficiente y devuelve None si no hay reultados.
    tercero_existente = Tercero.objects.filter(tipo_identificacion=tipo_id, nroid=nro_id).first()

    if tercero_existente:
        # Si lo encontramos, devolvemos que existe y también su nombre.
        return JsonResponse({
            'existe': True,
            'nombre': tercero_existente.nombre
        })
    else:
        # Si no lo encontramos, devolvemos que no existe.
        return JsonResponse({'existe': False})
