# C:/proyecto/Guia/terceros/tests.py
from django.test import TestCase, TransactionTestCase
from django.urls import reverse
from django.core.cache import cache
from django.db import connection
from django.test.utils import override_settings
from django.contrib.auth.models import User
from unittest.mock import patch, Mock
import json

from .models import Tercero, TipoTercero, TipoIdentificacion, Pais, Division, Ciudad
from .forms import TerceroForm


class QueryOptimizationTestCase(TestCase):
    """
    Tests específicos para validar que las optimizaciones de queries funcionen correctamente.
    """

    @classmethod
    def setUpTestData(cls):
        """Configuración de datos de prueba optimizada."""
        # Crear tipos básicos
        cls.tipo_tercero = TipoTercero.objects.create(nombre="Cliente")
        cls.tipo_id = TipoIdentificacion.objects.create(nombre="Cédula")

        # Crear geografía básica
        cls.pais = Pais.objects.create(nombre="Colombia", codigo_iso="CO", geoname_id=3686110)
        cls.division = Division.objects.create(
            nombre="Cundinamarca", codigo_iso="CO-CUN",
            geoname_id=3686210, pais=cls.pais
        )
        cls.ciudad = Ciudad.objects.create(
            nombre="Bogotá", geoname_id=3688689, division=cls.division
        )

        # Crear varios terceros para pruebas
        cls.terceros = []
        for i in range(10):
            tercero = Tercero.objects.create(
                tipo_tercero=cls.tipo_tercero,
                tipo_identificacion=cls.tipo_id,
                nroid=f"1000000{i}",
                nombre=f"Tercero {i}",
                ciudad=cls.ciudad,
                email=f"tercero{i}@test.com"
            )
            cls.terceros.append(tercero)

    def setUp(self):
        """Limpia cache antes de cada test."""
        cache.clear()

    def test_list_view_query_optimization(self):
        """Verifica que ListView use select_related correctamente."""
        url = reverse('terceros:Lista_terceros')

        # Resetear conexión para contar queries
        connection.queries_log.clear()

        with self.assertNumQueries(2):  # 1 query para datos + 1 para count (paginación)
            response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tercero 0")

        # Verificar que el query usa select_related
        query = connection.queries[0]['sql']
        self.assertIn('JOIN', query)  # Confirma que se hicieron JOINs

    def test_update_view_query_optimization(self):
        """Verifica que UpdateView precargue todas las relaciones."""
        tercero = self.terceros[0]
        url = reverse('terceros:editar_tercero', kwargs={'pk': tercero.pk})

        connection.queries_log.clear()

        with self.assertNumQueries(4):  # get_object + tipos_tercero + tipos_id + session
            response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        # El objeto debe tener sus relaciones precargadas
        # Acceder a estos campos no debe generar queries adicionales
        connection.queries_log.clear()

        tercero_from_context = response.context['object']
        _ = tercero_from_context.tipo_tercero.nombre  # No debe hacer query
        _ = tercero_from_context.ciudad.division.pais.nombre  # No debe hacer query

        # No debe haber queries adicionales
        self.assertEqual(len(connection.queries), 0)

    def test_dashboard_query_optimization(self):
        """Verifica que el dashboard use queries eficientes."""
        url = reverse('dashboard')

        connection.queries_log.clear()

        with self.assertNumQueries(4):  # stats + top_tipos + top_paises + session
            response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertIn('stats', response.context)

    def test_form_cache_optimization(self):
        """Verifica que el formulario use cache para tipos."""
        # Limpiar cache
        cache.clear()

        # Primera carga - debe hacer queries y cachear
        form1 = TerceroForm()

        # Segunda carga - debe usar cache
        connection.queries_log.clear()
        form2 = TerceroForm()

        # No debe haber queries para los tipos (están en cache)
        tipo_queries = [q for q in connection.queries if 'tipotercero' in q['sql'].lower()]
        self.assertEqual(len(tipo_queries), 0)


class APIPerformanceTestCase(TestCase):
    """Tests de performance para las APIs de GeoNames."""

    def setUp(self):
        cache.clear()

    @patch('terceros.views.requests.get')
    def test_geonames_cache_behavior(self, mock_get):
        """Verifica que las APIs de GeoNames usen cache correctamente."""
        # Mock de respuesta de la API
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'geonames': [
                {'geonameId': 123, 'countryName': 'Colombia', 'countryCode': 'CO'}
            ]
        }
        mock_get.return_value = mock_response

        url = reverse('terceros:api_buscar_paises')

        # Primera llamada - debe usar la API
        response1 = self.client.get(url, {'q': 'col'})
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(mock_get.call_count, 1)

        # Segunda llamada - debe usar cache (no llamar API)
        response2 = self.client.get(url, {'q': 'col'})
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(mock_get.call_count, 1)  # No aumenta

        # Los resultados deben ser iguales
        self.assertEqual(response1.json(), response2.json())

    def test_verification_api_performance(self):
        """Verifica que la API de verificación sea eficiente."""
        # Crear tercero de prueba
        tipo_tercero = TipoTercero.objects.create(nombre="Cliente")
        tipo_id = TipoIdentificacion.objects.create(nombre="Cédula")
        Tercero.objects.create(
            tipo_tercero=tipo_tercero,
            tipo_identificacion=tipo_id,
            nroid="12345678",
            nombre="Test User"
        )

        url = reverse('terceros:api_verificar_tercero')

        connection.queries_log.clear()

        # Debe usar solo 1 query optimizada
        with self.assertNumQueries(1):
            response = self.client.get(url, {'nroid': '12345678'})

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['existe'])
        self.assertEqual(data['nombre'], 'Test User')


class CacheInvalidationTestCase(TransactionTestCase):
    """Tests para validar la invalidación correcta del cache."""

    def setUp(self):
        cache.clear()

        # Crear datos base
        self.tipo_tercero = TipoTercero.objects.create(nombre="Cliente")
        self.tipo_id = TipoIdentificacion.objects.create(nombre="Cédula")

    def test_cache_invalidation_on_tercero_creation(self):
        """Verifica que se invalide el cache al crear terceros."""
        # Establecer datos en cache
        cache.set('dashboard_stats', {'test': 'data'}, 300)
        self.assertIsNotNone(cache.get('dashboard_stats'))

        # Crear tercero usando el formulario (que debe invalidar cache)
        form_data = {
            'tipo_tercero': self.tipo_tercero.pk,
            'tipo_identificacion': self.tipo_id.pk,
            'nroid': '87654321',
            'nombre': 'Test Cache Invalidation',
            'email': 'test@cache.com'
        }

        form = TerceroForm(data=form_data)
        self.assertTrue(form.is_valid())
        form.save()

        # El cache debe haberse invalidado
        self.assertIsNone(cache.get('dashboard_stats'))

    def test_cache_invalidation_api_endpoint(self):
        """Verifica que la API de invalidación funcione."""
        # Crear usuario staff
        user = User.objects.create_user('admin', 'admin@test.com', 'pass')
        user.is_staff = True
        user.save()

        self.client.login(username='admin', password='pass')

        # Establecer datos en cache
        cache.set('dashboard_stats', {'test': 'data'}, 300)
        cache.set(f'geonames_paises_test', [{'test': 'data'}], 300)

        # Llamar API de invalidación
        url = reverse('terceros:api_invalidar_cache')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('mensaje', data)

        # Verificar que el cache se invalidó
        self.assertIsNone(cache.get('dashboard_stats'))


class FormValidationTestCase(TestCase):
    """Tests para validaciones optimizadas en formularios."""

    @classmethod
    def setUpTestData(cls):
        cls.tipo_tercero = TipoTercero.objects.create(nombre="Cliente")
        cls.tipo_id = TipoIdentificacion.objects.create(nombre="Cédula")

        # Tercero existente para probar validaciones
        cls.tercero_existente = Tercero.objects.create(
            tipo_tercero=cls.tipo_tercero,
            tipo_identificacion=cls.tipo_id,
            nroid="11111111",
            nombre="Usuario Existente"
        )

    def test_unique_nroid_validation_performance(self):
        """Verifica que la validación de nroid único sea eficiente."""
        form_data = {
            'tipo_tercero': self.tipo_tercero.pk,
            'tipo_identificacion': self.tipo_id.pk,
            'nroid': '11111111',  # Número ya existente
            'nombre': 'Test Duplicado'
        }

        connection.queries_log.clear()

        form = TerceroForm(data=form_data)

        # La validación debe ser eficiente (solo 1 query de existencia)
        with self.assertNumQueries(1):
            is_valid = form.is_valid()

        self.assertFalse(is_valid)
        self.assertIn('nroid', form.errors)

    def test_form_choices_caching(self):
        """Verifica que las opciones del formulario usen cache."""
        cache.clear()

        # Primera instancia - debe cachear las opciones
        form1 = TerceroForm()

        # Segunda instancia - debe usar cache
        connection.queries_log.clear()
        form2 = TerceroForm()

        # No debe hacer queries para tipos (están en cache)
        self.assertEqual(len(connection.queries), 0)


class StressTestCase(TransactionTestCase):
    """Tests de estrés para validar performance bajo carga."""

    def test_bulk_tercero_creation_performance(self):
        """Verifica performance al crear múltiples terceros."""
        tipo_tercero = TipoTercero.objects.create(nombre="Cliente")
        tipo_id = TipoIdentificacion.objects.create(nombre="Cédula")

        terceros_data = []
        for i in range(100):
            terceros_data.append(
                Tercero(
                    tipo_tercero=tipo_tercero,
                    tipo_identificacion=tipo_id,
                    nroid=f"2000000{i:03d}",
                    nombre=f"Tercero Bulk {i}",
                    email=f"bulk{i}@test.com"
                )
            )

        # Creación en lote debe ser eficiente
        connection.queries_log.clear()

        with self.assertNumQueries(1):  # Solo 1 query para bulk_create
            Tercero.objects.bulk_create(terceros_data)

        # Verificar que se crearon correctamente
        self.assertEqual(Tercero.objects.filter(nombre__startswith="Tercero Bulk").count(), 100)

    def test_list_view_with_many_records(self):
        """Verifica performance de ListView con muchos registros."""
        # Crear datos de prueba
        tipo_tercero = TipoTercero.objects.create(nombre="Cliente")
        tipo_id = TipoIdentificacion.objects.create(nombre="Cédula")

        terceros = []
        for i in range(50):
            terceros.append(
                Tercero(
                    tipo_tercero=tipo_tercero,
                    tipo_identificacion=tipo_id,
                    nroid=f"3000000{i:03d}",
                    nombre=f"Tercero List {i}"
                )
            )
        Tercero.objects.bulk_create(terceros)

        url = reverse('terceros:Lista_terceros')

        connection.queries_log.clear()

        # Debe mantener el número de queries bajo independientemente del volumen
        with self.assertNumQueries(2):  # select + count para paginación
            response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        # Verificar paginación
        self.assertIn('is_paginated', response.context)


# Utilidad para tests de performance
class QueryCountMixin:
    """Mixin para facilitar el conteo de queries en tests."""

    def assertMaxQueries(self, max_queries, callable_obj=None):
        """Verifica que no se excedan un número máximo de queries."""
        connection.queries_log.clear()

        if callable_obj:
            callable_obj()

        actual_queries = len(connection.queries)
        self.assertLessEqual(
            actual_queries,
            max_queries,
            f"Se ejecutaron {actual_queries} queries, máximo esperado: {max_queries}"
        )

    def print_queries(self):
        """Utilidad para debug - imprime todas las queries ejecutadas."""
        for i, query in enumerate(connection.queries):
            print(f"Query {i + 1}: {query['sql']}")
            print(f"Time: {query['time']}")
            print("---")