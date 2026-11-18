import json
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse

from contenido.models import Mundo, Temario, Actividad, ProgresoActividad
from login.models import Usuario
from .models import CodeBreaker, ConceptoCodeBreaker, TipoConcepto
from .operaciones.OperacionesCodeBreaker import OperacionesCodeBreaker
from .datos import CONCEPTOS_CODEBREAKER


class CodeBreakerOperacionesTests(TestCase):
    def setUp(self):
        self.mundo = Mundo.objects.create(nombre="Mundo Pruebas", orden=1)
        self.temario = Temario.objects.create(mundo=self.mundo, nombre="Temario Calidad", orden=1)
        self.actividad = Actividad.objects.create(
            temario=self.temario,
            tipo="codebreaker",
            titulo="CodeBreaker",
            orden=1,
            puntos_max=100
        )
        self.siguiente_actividad = Actividad.objects.create(
            temario=self.temario,
            tipo="crucigrama",
            titulo="Siguiente Actividad",
            orden=2,
            puntos_max=100
        )
        self.user = User.objects.create_user(username="jugador1", password="password123")
        self.usuario_perfil = Usuario.objects.create(cuenta=self.user, nombre="Jugador 1", email="j1@test.com")

        self.cb = CodeBreaker.objects.create(
            actividad=self.actividad,
            filas=6,
            columnas=10,
            bloques_totales=60,
            bloques_especiales=8
        )
        for c in CONCEPTOS_CODEBREAKER:
            ConceptoCodeBreaker.objects.create(
                codebreaker=self.cb,
                nombre=c["nombre"],
                nombre_corto=c["nombre_corto"],
                tipo=c["tipo"],
                efecto_clave=c["efecto_clave"],
                efecto_descripcion=c["efecto_descripcion"],
                definicion=c["definicion"],
                explicacion=c["explicacion"],
                tipo_ejemplo=c.get("tipo_ejemplo", "Ejemplo"),
                ejemplo=c["ejemplo"],
                color=c.get("color", "#5b5bf0")
            )

    def test_regla_rn111_calculo_xp(self):
        """RN-111: Máximo 100 XP, cada vida perdida descuenta 10 XP, solo al completar."""
        self.assertEqual(OperacionesCodeBreaker.calcular_xp(vidas_perdidas=0, completada=True), 100)
        self.assertEqual(OperacionesCodeBreaker.calcular_xp(vidas_perdidas=1, completada=True), 90)
        self.assertEqual(OperacionesCodeBreaker.calcular_xp(vidas_perdidas=2, completada=True), 80)
        self.assertEqual(OperacionesCodeBreaker.calcular_xp(vidas_perdidas=3, completada=True), 70)
        # RN-107: Si no se completa, no se otorga XP
        self.assertEqual(OperacionesCodeBreaker.calcular_xp(vidas_perdidas=0, completada=False), 0)
        self.assertEqual(OperacionesCodeBreaker.calcular_xp(vidas_perdidas=3, completada=False), 0)

    def test_regla_rn96_y_rn97_distribucion_conceptos(self):
        """RN-96 y RN-97: 8 conceptos en total, 6 positivos y 2 negativos."""
        conceptos = self.cb.conceptos.all()
        self.assertEqual(conceptos.count(), 8)
        positivos = conceptos.filter(tipo=TipoConcepto.POSITIVO).count()
        negativos = conceptos.filter(tipo=TipoConcepto.NEGATIVO).count()
        self.assertEqual(positivos, 6)
        self.assertEqual(negativos, 2)

    def test_registro_resultado_completado_y_desbloqueo(self):
        """RN-108, RN-113: Registra resultado y desbloquea siguiente actividad al completar."""
        res = OperacionesCodeBreaker.registrar_resultado(
            actividad=self.actividad,
            usuario_cuenta=self.user,
            vidas_perdidas=1,
            conceptos_ids=[1, 2, 3],
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

    def test_registro_resultado_partida_perdida(self):
        """RN-107: Si el jugador pierde todas las vidas, queda en_progreso y 0 XP."""
        res = OperacionesCodeBreaker.registrar_resultado(
            actividad=self.actividad,
            usuario_cuenta=self.user,
            vidas_perdidas=3,
            conceptos_ids=[1],
            completada=False
        )
        self.assertTrue(res["ok"])
        self.assertEqual(res["xp"], 0)
        self.assertFalse(res["siguiente_desbloqueada"])

        progreso = ProgresoActividad.objects.get(actividad=self.actividad, usuario=self.usuario_perfil)
        self.assertEqual(progreso.estado, "en_progreso")
        self.assertEqual(progreso.puntaje, 0)
        self.assertIsNone(progreso.fecha_completado)

    def test_vista_codebreaker_renderiza_correctamente(self):
        """Flujo normal paso 1 y 2: Recupera la actividad y muestra pantalla inicial."""
        client = Client()
        client.force_login(self.user)
        url = reverse("codebreaker:jugar", kwargs={"actividad_id": self.actividad.id})
        response = client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "codebreaker/codebreaker.html")
        self.assertIn("conceptos_json", response.context)
        self.assertContains(response, "CodeBreaker")

    def test_vista_codebreaker_excepcion_carga(self):
        """Excepción 1.0.E1: Si no tiene conceptos o no existe CodeBreaker, redirige al temario."""
        act_vacia = Actividad.objects.create(
            temario=self.temario,
            tipo="codebreaker",
            titulo="Actividad Vacía",
            orden=3,
            puntos_max=100
        )
        client = Client()
        client.force_login(self.user)
        url = reverse("codebreaker:jugar", kwargs={"actividad_id": act_vacia.id})
        response = client.get(url)
        # Debe redirigir al temario
        self.assertEqual(response.status_code, 302)

    def test_endpoint_finalizar_partida_api(self):
        """Llamada POST al endpoint finalizar partida."""
        client = Client()
        client.force_login(self.user)
        url = reverse("codebreaker:finalizar", kwargs={"actividad_id": self.actividad.id})
        payload = {
            "vidas_perdidas": 2,
            "conceptos_ids": [1, 2],
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
        self.assertEqual(data["xp"], 80)
        self.assertTrue(data["completada"])

    def test_endpoint_datos_partida(self):
        """Endpoint de datos JSON de la partida."""
        client = Client()
        client.force_login(self.user)
        url = reverse("codebreaker:datos", kwargs={"actividad_id": self.actividad.id})
        response = client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["ok"])
        self.assertEqual(data["filas"], 6)
        self.assertEqual(data["columnas"], 10)
        self.assertEqual(len(data["conceptos"]), 8)
