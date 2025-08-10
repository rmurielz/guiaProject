from django.test import TestCase
from django.urls import reverse
from .models import Tercero, TipoIdentificacion, TipoTercero

class TerceroViewsTestCase(TestCase):

    def setUp(self):
        """
        Configuración inicial para las pruebas. Se ejecuta antes de cada test.
        Creamos los objetos necesarios para las pruebas.
        """
        self.tipo_id = TipoIdentificacion.objects.create(nombre='Cédula de Ciudadanía')
        self.tipo_tercero = TipoTercero.objects.create(nombre='Cliente')

        # Creamos un tercero activo y uno inactivo
        self.tercero_activo = Tercero.objects.create(
            nombre='Tercero Activo de Prueba',
            nroid='12345',
            tipo_identificacion=self.tipo_id,
            tipo_tercero=self.tipo_tercero,
            activo=True
        )
        self.tercero_inactivo = Tercero.objects.create(
            nombre='Tercero Inactivo de Prueba',
            nroid='67890',
            tipo_identificacion=self.tipo_id,
            tipo_tercero=self.tipo_tercero,
            activo=False
        )

    def test_tercero_list_view_status_code(self):
        """Verifica que la página de la lista de terceros carga correctamente."""
        response = self.client.get(reverse('terceros:Lista_terceros'))
        self.assertEqual(response.status_code, 200)

    def test_tercero_list_view_shows_only_active(self):
        """Verifica que la lista solo muestra terceros activos."""
        response = self.client.get(reverse('terceros:Lista_terceros'))

        # Comprueba que el tercero activo está en el contexto de la plantilla
        self.assertContains(response, self.tercero_activo.nombre)
        # Comprueba que el tercero inactivo NO está
        self.assertNotContains(response, self.tercero_inactivo.nombre)