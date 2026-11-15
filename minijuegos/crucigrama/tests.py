from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse

from contenido.models import Mundo, Temario, Actividad, ProgresoActividad
from login.models import Usuario
from minijuegos.crucigrama.models import Crucigrama, PalabraCrucigrama
from minijuegos.crucigrama.operaciones.OperacionesCrucigrama import OperacionesCrucigrama


class OperacionesCrucigramaTests(TestCase):
    """Tests para la lógica de negocio del crucigrama (RN-52 a RN-66)."""

    def test_normalizar_rn53(self):
        """RN-53: No distingue mayúsculas/minúsculas ni acentos."""
        self.assertEqual(OperacionesCrucigrama.normalizar("Excepción"), "EXCEPCION")
        self.assertEqual(OperacionesCrucigrama.normalizar("actor"), "ACTOR")
        self.assertEqual(OperacionesCrucigrama.normalizar("FLUJO"), "FLUJO")
        self.assertEqual(OperacionesCrucigrama.normalizar("  Include  "), "INCLUDE")

    def test_validar_palabra_rn53_rn54(self):
        """RN-53, RN-54: Validación de palabra sin distinguir mayúsculas ni acentos."""
        self.assertTrue(OperacionesCrucigrama.validar_palabra("excepcion", "EXCEPCIÓN"))
        self.assertTrue(OperacionesCrucigrama.validar_palabra("ACTOR", "actor"))
        self.assertFalse(OperacionesCrucigrama.validar_palabra("ACTO", "ACTOR"))

    def test_calcular_xp_rn64_rn65(self):
        """RN-64: XP = 100 / total * primer_intento. RN-65: Solo primer intento."""
        # 8 palabras, todas al primer intento -> 100 XP
        self.assertEqual(OperacionesCrucigrama.calcular_xp(8, 8), 100)
        # 8 palabras, 4 al primer intento -> 50 XP
        self.assertEqual(OperacionesCrucigrama.calcular_xp(4, 8), 50)
        # 8 palabras, 0 al primer intento -> 0 XP
        self.assertEqual(OperacionesCrucigrama.calcular_xp(0, 8), 0)
        # 8 palabras, 6 al primer intento -> 75 XP
        self.assertEqual(OperacionesCrucigrama.calcular_xp(6, 8), 75)

    def test_calcular_xp_casos_borde(self):
        """Casos borde del cálculo de XP."""
        self.assertEqual(OperacionesCrucigrama.calcular_xp(0, 0), 0)
        self.assertEqual(OperacionesCrucigrama.calcular_xp(-1, 5), 0)
        self.assertEqual(OperacionesCrucigrama.calcular_xp("invalido", 5), 0)

    def test_es_intento_repetido_rn57(self):
        """RN-57: Intento incorrecto idéntico no resta vida."""
        intentos = ["ACTRO", "ACTORY"]
        self.assertTrue(OperacionesCrucigrama.es_intento_repetido(intentos, "ACTRO"))
        self.assertFalse(OperacionesCrucigrama.es_intento_repetido(intentos, "ACTR"))

    def test_validar_resultado(self):
        """Validar consistencia de los datos del cliente."""
        self.assertTrue(OperacionesCrucigrama.validar_resultado(5, 8, 2))
        self.assertTrue(OperacionesCrucigrama.validar_resultado(8, 8, 0))
        self.assertFalse(OperacionesCrucigrama.validar_resultado(9, 8, 2))
        self.assertFalse(OperacionesCrucigrama.validar_resultado(-1, 8, 2))
        self.assertFalse(OperacionesCrucigrama.validar_resultado("a", 8, 2))


class CrucigramaViewsTests(TestCase):
    """Tests de integración para las vistas del crucigrama."""

    def setUp(self):
        self.user = User.objects.create_user(username="jugador", password="password123")
        self.usuario = Usuario.objects.create(
            nombre="Jugador Test", email="jugador@test.com", cuenta=self.user
        )
        self.mundo = Mundo.objects.create(nombre="Mundo 2: Casos de uso", orden=2)
        self.temario = Temario.objects.create(mundo=self.mundo, nombre="Unidad 1", orden=1)
        self.actividad = Actividad.objects.create(
            temario=self.temario,
            tipo="crucigrama",
            titulo="Crucigrama: Casos de uso",
            orden=1,
            puntos_max=100,
        )
        self.crucigrama = Crucigrama.objects.create(
            actividad=self.actividad,
            filas=13,
            columnas=10,
            tiempo_limite_seg=180,
        )
        # Crear 2 palabras de prueba
        PalabraCrucigrama.objects.create(
            crucigrama=self.crucigrama,
            numero=1,
            direccion='v',
            fila_inicio=0,
            columna_inicio=0,
            respuesta="EXTEND",
            enunciado="Relación extend en UML.",
            explicacion="Extend indica que un CU puede ampliar a otro.",
        )
        PalabraCrucigrama.objects.create(
            crucigrama=self.crucigrama,
            numero=2,
            direccion='h',
            fila_inicio=5,
            columna_inicio=0,
            respuesta="ACTOR",
            enunciado="Persona o sistema externo.",
            explicacion="El actor interactúa con el sistema.",
        )

        self.client = Client()
        self.client.login(username="jugador", password="password123")

    def test_vista_crucigrama_get(self):
        """CU-09: El sistema recupera el crucigrama y muestra la vista."""
        url = reverse("crucigrama:jugar", kwargs={"actividad_id": self.actividad.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Crucigrama")

    def test_vista_crucigrama_sin_datos(self):
        """Excepción 1.0.E1: Redirige si no hay datos."""
        # Crear actividad sin crucigrama
        actividad2 = Actividad.objects.create(
            temario=self.temario,
            tipo="crucigrama",
            titulo="Crucigrama vacío",
            orden=2,
            puntos_max=100,
        )
        url = reverse("crucigrama:jugar", kwargs={"actividad_id": actividad2.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # Redirect al temario

    def test_finalizar_partida_completada(self):
        """CU-09: Finalizar crucigrama completado correctamente."""
        url = reverse("crucigrama:finalizar", kwargs={"actividad_id": self.actividad.pk})
        payload = {
            "palabras_resueltas": 2,
            "palabras_primer_intento": 2,
            "vidas_restantes": 3,
            "vidas_perdidas": 0,
            "tiempo_empleado": 90,
            "completado": True,
        }
        response = self.client.post(url, data=payload, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["puntaje"], 100)
        self.assertTrue(data["completado"])

        progreso = ProgresoActividad.objects.get(
            usuario=self.usuario, actividad=self.actividad
        )
        self.assertEqual(progreso.puntaje, 100)
        self.assertEqual(progreso.estado, "completado")
        self.assertIsNotNone(progreso.fecha_completado)

    def test_finalizar_partida_derrota(self):
        """CU-09 FA 1.3: Sin vidas, no se completa."""
        url = reverse("crucigrama:finalizar", kwargs={"actividad_id": self.actividad.pk})
        payload = {
            "palabras_resueltas": 1,
            "palabras_primer_intento": 0,
            "vidas_restantes": 0,
            "vidas_perdidas": 3,
            "tiempo_empleado": 120,
            "completado": False,
        }
        response = self.client.post(url, data=payload, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["puntaje"], 0)
        self.assertFalse(data["completado"])

        progreso = ProgresoActividad.objects.get(
            usuario=self.usuario, actividad=self.actividad
        )
        self.assertEqual(progreso.estado, "en_progreso")
