from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse

from contenido.models import Mundo, Temario, Actividad, ProgresoActividad
from login.models import Usuario
from minijuegos.snake.models import Snake, NivelSnake, ItemNivel
from minijuegos.snake.operaciones.OperacionesSnake import OperacionesSnake


class OperacionesSnakeTests(TestCase):
    def test_calcular_puntaje_rn18(self):
        # 0 objetivos de 4 -> 0 XP
        self.assertEqual(OperacionesSnake.calcular_puntaje(0, 4), 0)
        # 1 objetivo de 4 -> 25 XP
        self.assertEqual(OperacionesSnake.calcular_puntaje(1, 4), 25)
        # 2 objetivos de 4 -> 50 XP
        self.assertEqual(OperacionesSnake.calcular_puntaje(2, 4), 50)
        # 3 objetivos de 4 -> 75 XP
        self.assertEqual(OperacionesSnake.calcular_puntaje(3, 4), 75)
        # 4 objetivos de 4 -> 100 XP
        self.assertEqual(OperacionesSnake.calcular_puntaje(4, 4), 100)

    def test_calcular_puntaje_casos_borde(self):
        # Total 0
        self.assertEqual(OperacionesSnake.calcular_puntaje(0, 0), 0)
        # Negativos o invalidos
        self.assertEqual(OperacionesSnake.calcular_puntaje(-1, 5), 0)
        self.assertEqual(OperacionesSnake.calcular_puntaje("invalido", 5), 0)

    def test_validar_resultado(self):
        self.assertTrue(OperacionesSnake.validar_resultado(2, 4))
        self.assertTrue(OperacionesSnake.validar_resultado(4, 4))
        self.assertFalse(OperacionesSnake.validar_resultado(5, 4))
        self.assertFalse(OperacionesSnake.validar_resultado(-1, 4))
        self.assertFalse(OperacionesSnake.validar_resultado("a", 4))


class SnakeViewsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="jugador", password="password123")
        self.usuario = Usuario.objects.create(nombre="Jugador Test", email="jugador@test.com", cuenta=self.user)
        self.mundo = Mundo.objects.create(nombre="Mundo 1: Requerimientos", orden=1)
        self.temario = Temario.objects.create(mundo=self.mundo, nombre="Unidad 1", orden=1)
        self.actividad = Actividad.objects.create(
            temario=self.temario,
            tipo="snake",
            titulo="Cazador Snake",
            orden=1,
            puntos_max=100
        )
        self.snake = Snake.objects.create(actividad=self.actividad)
        self.nivel = NivelSnake.objects.create(
            snake=self.snake,
            numero=1,
            titulo="Nivel 1: Identificar RNF",
            tema="Requerimientos",
            instrucciones="Recolecta los RNF y esquiva los RF.",
            filas=20,
            columnas=20,
            velocidad_ms=180
        )
        # 2 Objetivos RNF
        ItemNivel.objects.create(
            nivel=self.nivel,
            identificador="RNF-01",
            categoria="Rendimiento",
            texto="Tiempo de respuesta menor a 1 segundo.",
            es_objetivo=True,
            explicacion="Es una restricción de desempeño."
        )
        ItemNivel.objects.create(
            nivel=self.nivel,
            identificador="RNF-02",
            categoria="Seguridad",
            texto="Contraseñas cifradas con Argon2.",
            es_objetivo=True,
            explicacion="Es una restricción de seguridad."
        )
        # 1 Obstaculo RF
        ItemNivel.objects.create(
            nivel=self.nivel,
            identificador="RF-01",
            categoria="Gestión",
            texto="El usuario puede iniciar sesión.",
            es_objetivo=False,
            explicacion="Es una funcionalidad del usuario.",
            contraste="Los RF definen qué hace el sistema."
        )

        self.client = Client()
        self.client.login(username="jugador", password="password123")

    def test_vista_snake_get(self):
        url = reverse("snake:jugar", kwargs={"actividad_id": self.actividad.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cazador Snake")
        self.assertContains(response, "Nivel 1: Identificar RNF")

    def test_finalizar_partida_derrota_con_puntaje_parcial(self):
        url = reverse("snake:finalizar", kwargs={"actividad_id": self.actividad.pk})
        # Jugador recogió 1 de 2 RNF (50 XP) y chocó contra muro
        payload = {
            "nivel_id": self.nivel.pk,
            "objetivos_recolectados": 1,
            "motivo_fin": OperacionesSnake.MOTIVO_CHOQUE_MURO,
            "segundos": 15
        }
        response = self.client.post(url, data=payload, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["puntaje"], 50)
        self.assertEqual(data["mejor_puntaje"], 50)
        self.assertFalse(data["es_victoria"])

        progreso = ProgresoActividad.objects.get(usuario=self.usuario, actividad=self.actividad)
        self.assertEqual(progreso.puntaje, 50)
        self.assertEqual(progreso.intentos, 1)
        self.assertEqual(progreso.estado, "en_progreso")

    def test_finalizar_partida_victoria(self):
        url = reverse("snake:finalizar", kwargs={"actividad_id": self.actividad.pk})
        # Jugador recogió 2 de 2 RNF (100 XP) y ganó
        payload = {
            "nivel_id": self.nivel.pk,
            "objetivos_recolectados": 2,
            "motivo_fin": OperacionesSnake.MOTIVO_TODOS_OBJETIVOS,
            "segundos": 25
        }
        response = self.client.post(url, data=payload, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["puntaje"], 100)
        self.assertTrue(data["es_victoria"])

        progreso = ProgresoActividad.objects.get(usuario=self.usuario, actividad=self.actividad)
        self.assertEqual(progreso.puntaje, 100)
        self.assertEqual(progreso.estado, "completado")
        self.assertIsNotNone(progreso.fecha_completado)
