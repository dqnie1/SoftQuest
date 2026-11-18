import json
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse

from contenido.models import Mundo, Temario, Actividad, ProgresoActividad
from login.models import Usuario
from .models import SopaLetras, PalabraSopa
from .operaciones.OperacionesSopaLetras import OperacionesSopaLetras
from .datos import PALABRAS_SOPALETRAS


class SopaLetrasOperacionesTests(TestCase):
    def setUp(self):
        self.mundo = Mundo.objects.create(nombre="Mundo Pruebas", orden=1)
        self.temario = Temario.objects.create(mundo=self.mundo, nombre="Temario Fundamentos", orden=1)
        self.actividad = Actividad.objects.create(
            temario=self.temario,
            tipo="sopaletras",
            titulo="Sopa de Letras",
            orden=1,
            puntos_max=100
        )
        self.siguiente_actividad = Actividad.objects.create(
            temario=self.temario,
            tipo="trivia",
            titulo="Trivia Siguiente",
            orden=2,
            puntos_max=100
        )
        self.user = User.objects.create_user(username="jugador_sopa", password="password123")
        self.usuario_perfil = Usuario.objects.create(cuenta=self.user, nombre="Jugador Sopa", email="sopa@test.com")

        self.sopa = SopaLetras.objects.create(
            actividad=self.actividad,
            dimension=12,
            total_palabras=8
        )
        for p in PALABRAS_SOPALETRAS:
            PalabraSopa.objects.create(
                sopaletras=self.sopa,
                palabra=p["palabra"],
                nombre=p["nombre"],
                definicion=p["definicion"],
                explicacion=p["explicacion"],
                tipo_ejemplo=p.get("tipo_ejemplo", "Ejemplo"),
                ejemplo=p["ejemplo"],
                color=p.get("color", "#818cf8")
            )

    def test_regla_rn92_calculo_xp(self):
        """RN-92: Cada error descuenta 5 XP, sin que el XP pueda ser menor a 0."""
        self.assertEqual(OperacionesSopaLetras.calcular_xp(errores=0, completada=True), 100)
        self.assertEqual(OperacionesSopaLetras.calcular_xp(errores=1, completada=True), 95)
        self.assertEqual(OperacionesSopaLetras.calcular_xp(errores=4, completada=True), 80)
        self.assertEqual(OperacionesSopaLetras.calcular_xp(errores=20, completada=True), 0)
        self.assertEqual(OperacionesSopaLetras.calcular_xp(errores=25, completada=True), 0)
        # Si no se completa, 0 XP
        self.assertEqual(OperacionesSopaLetras.calcular_xp(errores=0, completada=False), 0)

    def test_regla_rn81_dimension_y_palabras(self):
        """RN-81: Dimensión 12x12 y 8 palabras en total."""
        self.assertEqual(self.sopa.dimension, 12)
        self.assertEqual(self.sopa.total_palabras, 8)
        self.assertEqual(self.sopa.palabras.count(), 8)

    def test_registro_resultado_completado_y_desbloqueo(self):
        """RN-93: Registra resultado y desbloquea siguiente actividad al completar."""
        res = OperacionesSopaLetras.registrar_resultado(
            actividad=self.actividad,
            usuario_cuenta=self.user,
            errores=2,
            pista_usada=True,
            tiempo_segundos=120,
            completada=True
        )
        self.assertTrue(res["ok"])
        self.assertEqual(res["xp"], 90)
        self.assertTrue(res["siguiente_desbloqueada"])

        progreso = ProgresoActividad.objects.get(actividad=self.actividad, usuario=self.usuario_perfil)
        self.assertEqual(progreso.estado, "completado")
        self.assertEqual(progreso.puntaje, 90)
        self.assertIsNotNone(progreso.fecha_completado)

        # Siguiente actividad debe estar disponible
        progreso_sig = ProgresoActividad.objects.get(actividad=self.siguiente_actividad, usuario=self.usuario_perfil)
        self.assertEqual(progreso_sig.estado, "disponible")

    def test_vista_sopaletras_renderiza_correctamente(self):
        """Flujo normal paso 1 y 2: Recupera la actividad y muestra pantalla inicial."""
        client = Client()
        client.force_login(self.user)
        url = reverse("sopaletras:jugar", kwargs={"actividad_id": self.actividad.id})
        response = client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "sopaletras/sopaletras.html")
        self.assertIn("palabras_json", response.context)
        self.assertContains(response, "Sopa de letras")

    def test_vista_sopaletras_excepcion_carga(self):
        """Excepción 1.0.E1: Si no tiene palabras o no existe SopaLetras, redirige al temario."""
        act_vacia = Actividad.objects.create(
            temario=self.temario,
            tipo="sopaletras",
            titulo="Actividad Vacía",
            orden=3,
            puntos_max=100
        )
        client = Client()
        client.force_login(self.user)
        url = reverse("sopaletras:jugar", kwargs={"actividad_id": act_vacia.id})
        response = client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_endpoint_finalizar_partida_api(self):
        """Llamada POST al endpoint finalizar partida."""
        client = Client()
        client.force_login(self.user)
        url = reverse("sopaletras:finalizar", kwargs={"actividad_id": self.actividad.id})
        payload = {
            "errores": 3,
            "pista_usada": False,
            "tiempo_segundos": 95,
            "completada": True
        }
        response = client.post(
            url,
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["ok"])
        self.assertEqual(data["xp"], 85)
        self.assertTrue(data["completada"])

    def test_endpoint_datos_partida(self):
        """Endpoint de datos JSON de la partida."""
        client = Client()
        client.force_login(self.user)
        url = reverse("sopaletras:datos", kwargs={"actividad_id": self.actividad.id})
        response = client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["ok"])
        self.assertEqual(data["dimension"], 12)
        self.assertEqual(data["total_palabras"], 8)
        self.assertEqual(len(data["palabras"]), 8)
