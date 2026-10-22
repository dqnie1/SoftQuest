import json
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from contenido.models import Actividad, Mundo, ProgresoActividad, Temario
from login.models import Usuario
from minijuegos.nave.models import (
    AnomaliaAmbigua,
    NaveEspacial,
    OpcionMetrica,
    Requerimiento,
    TipoRequerimiento,
)
from minijuegos.nave.operaciones.OperacionesNave import EstadoPartida, OperacionesNave


class OperacionesNaveTestCase(TestCase):
    """Pruebas unitarias para la lógica de negocio OperacionesNave (sin dependencias de request)."""

    def setUp(self):
        self.mundo = Mundo.objects.create(nombre="Mundo Req", orden=1)
        self.temario = Temario.objects.create(mundo=self.mundo, nombre="Temario Req", orden=1)
        self.actividad = Actividad.objects.create(
            temario=self.temario,
            tipo="nave_espacial",
            titulo="Nave Test",
            orden=1,
            puntos_max=100,
        )
        self.nave = NaveEspacial.objects.create(actividad=self.actividad)

        # Crear requerimientos de prueba
        self.req_rf = Requerimiento.objects.create(
            nave_espacial=self.nave,
            texto="Exportar PDF",
            tipo=TipoRequerimiento.RF,
            explicacion="Servicio funcional",
        )
        self.req_rnf = Requerimiento.objects.create(
            nave_espacial=self.nave,
            texto="Tiempo < 2s",
            tipo=TipoRequerimiento.RNF,
            explicacion="Rendimiento",
        )
        self.req_rn = Requerimiento.objects.create(
            nave_espacial=self.nave,
            texto="Solo mayores de edad",
            tipo=TipoRequerimiento.RN,
            explicacion="Regla legal",
        )

        # Crear anomalía de prueba con opciones
        self.anomalia = AnomaliaAmbigua.objects.create(
            nave_espacial=self.nave,
            texto_ambiguo="Debe ser muy rápido",
            explicacion="Falta métrica cuantitativa",
            tiempo_limite_seg=5,
        )
        self.opc_correcta = OpcionMetrica.objects.create(
            anomalia=self.anomalia,
            texto="Latencia < 100ms",
            es_correcta=True,
        )
        self.opc_incorrecta = OpcionMetrica.objects.create(
            anomalia=self.anomalia,
            texto="Usar buen hardware",
            es_correcta=False,
        )

    def test_iniciar_partida(self):
        estado = OperacionesNave.iniciarPartida()
        self.assertEqual(estado.escudo, OperacionesNave.ESCUDO_INICIAL)
        self.assertEqual(estado.combo, OperacionesNave.COMBO_INICIAL)
        self.assertEqual(estado.puntaje, 0)
        self.assertEqual(estado.aciertos_rf, 0)
        self.assertEqual(estado.aciertos_rnf, 0)
        self.assertEqual(estado.aciertos_rn, 0)
        self.assertFalse(estado.partida_terminada)

    def test_validar_clasificacion_correcta_incrementa_puntaje_y_combo(self):
        estado = OperacionesNave.iniciarPartida()

        # Primer acierto: puntaje += 150 * 1 = 150, luego combo pasa a 2
        correcto, exp, tipo, estado = OperacionesNave.validarClasificacion('RF', self.req_rf.id, estado)
        self.assertTrue(correcto)
        self.assertEqual(tipo, 'RF')
        self.assertEqual(estado.puntaje, 150)
        self.assertEqual(estado.combo, 2)
        self.assertEqual(estado.aciertos_rf, 1)

        # Segundo acierto: puntaje += 150 * 2 = 300 (total 450), combo pasa a 3
        correcto, _, _, estado = OperacionesNave.validarClasificacion('RNF', self.req_rnf.id, estado)
        self.assertTrue(correcto)
        self.assertEqual(estado.puntaje, 450)
        self.assertEqual(estado.combo, 3)
        self.assertEqual(estado.aciertos_rnf, 1)

    def test_validar_clasificacion_incorrecta_reduce_escudo_y_reinicia_combo(self):
        estado = EstadoPartida(escudo=100, combo=3, puntaje=500)
        correcto, exp, tipo, estado = OperacionesNave.validarClasificacion('RN', self.req_rf.id, estado)
        self.assertFalse(correcto)
        self.assertEqual(tipo, 'RF')
        self.assertEqual(estado.escudo, 90)
        self.assertEqual(estado.combo, 1)
        self.assertEqual(estado.puntaje, 500)

    def test_validar_metrica_anomalia(self):
        estado = EstadoPartida(escudo=100, combo=2, puntaje=100)
        # Correcta: puntaje += 500 (plano), combo pasa a 3
        correcta, exp, opc_id, estado = OperacionesNave.validarMetrica(
            self.opc_correcta.id, self.anomalia.id, estado
        )
        self.assertTrue(correcta)
        self.assertEqual(opc_id, self.opc_correcta.id)
        self.assertEqual(estado.puntaje, 600)
        self.assertEqual(estado.combo, 3)

        # Incorrecta: escudo - 10, combo = 1
        correcta, exp, opc_id, estado = OperacionesNave.validarMetrica(
            self.opc_incorrecta.id, self.anomalia.id, estado
        )
        self.assertFalse(correcta)
        self.assertEqual(estado.escudo, 90)
        self.assertEqual(estado.combo, 1)

    def test_penalizar_escudo_motivos_validos_e_invalidos(self):
        estado = OperacionesNave.iniciarPartida()

        for motivo in ["tiempo_agotado", "no_interceptado", "impacto_nave"]:
            estado = OperacionesNave.penalizarEscudo(motivo, estado)
            self.assertEqual(estado.combo, 1)

        self.assertEqual(estado.escudo, 70)

        # Motivo no válido levanta ValueError
        with self.assertRaises(ValueError):
            OperacionesNave.penalizarEscudo("motivo_invalido", estado)

    def test_escudo_llega_a_cero_termina_partida_y_rechaza_eventos(self):
        estado = EstadoPartida(escudo=10, combo=2)
        estado = OperacionesNave.penalizarEscudo("impacto_nave", estado)
        self.assertEqual(estado.escudo, 0)
        self.assertTrue(estado.partida_terminada)

        # Evento nuevo rechazado
        correcto, _, _, estado = OperacionesNave.validarClasificacion('RF', self.req_rf.id, estado)
        self.assertFalse(correcto)
        self.assertEqual(estado.escudo, 0)

    def test_calcular_precision(self):
        estado = EstadoPartida(
            aciertos_rf=2,
            aciertos_rnf=1,
            aciertos_rn=0,
        )
        # Se generaron: 2 veces req_rf (RF), 2 veces req_rnf (RNF), 1 vez req_rn (RN)
        gen = {
            str(self.req_rf.id): 2,
            str(self.req_rnf.id): 2,
            str(self.req_rn.id): 1,
        }
        res = OperacionesNave.calcularPrecision(estado, gen)
        self.assertEqual(res['precision_rf'], 100.0)  # 2/2
        self.assertEqual(res['precision_rnf'], 50.0)  # 1/2
        self.assertEqual(res['precision_rn'], 0.0)    # 0/1
        self.assertEqual(res['precision_global'], 60.0)  # 3/5 = 60.0%

    def test_calcular_xp_casos_especificados(self):
        """Casos de prueba obligatorios dados en la especificación."""
        casos = [
            (90, 5000, 70),
            (100, 3000, 65),
            (70, 12000, 85),
            (60, 2000, 40),
        ]
        for prec, pts, exp in casos:
            st = EstadoPartida(puntaje=pts)
            xp = OperacionesNave.calcularXP(st, prec)
            self.assertEqual(xp, exp, f"Fallo en prec={prec}, pts={pts}. Obtenido {xp}, esperado {exp}")


class ViewNaveTestCase(TestCase):
    """Pruebas de integración HTTP y endpoints de ViewNave."""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="player1", password="secretpassword"
        )
        self.perfil = Usuario.objects.create(
            nombre="Player One", email="player@softquest.com", cuenta=self.user
        )
        self.mundo = Mundo.objects.create(nombre="Mundo Test", orden=1)
        self.temario = Temario.objects.create(mundo=self.mundo, nombre="Temario Test", orden=1)
        self.actividad = Actividad.objects.create(
            temario=self.temario,
            tipo="nave_espacial",
            titulo="Requirements Cyber-Defense",
            orden=1,
            puntos_max=100,
        )
        self.siguiente_actividad = Actividad.objects.create(
            temario=self.temario,
            tipo="trivia",
            titulo="Siguiente Actividad",
            orden=2,
            puntos_max=100,
        )
        self.nave = NaveEspacial.objects.create(actividad=self.actividad)
        self.req = Requerimiento.objects.create(
            nave_espacial=self.nave,
            texto="El usuario debe poder iniciar sesión",
            tipo=TipoRequerimiento.RF,
            explicacion="Función directa del sistema",
        )
        self.anomalia = AnomaliaAmbigua.objects.create(
            nave_espacial=self.nave,
            texto_ambiguo="Rápido",
            explicacion="Métrica de tiempo requerida",
            tiempo_limite_seg=5,
        )
        self.opc_corr = OpcionMetrica.objects.create(
            anomalia=self.anomalia, texto="< 2s", es_correcta=True
        )
        self.opc_inc = OpcionMetrica.objects.create(
            anomalia=self.anomalia, texto="veloz", es_correcta=False
        )

        self.client = Client()
        self.client.login(username="player1", password="secretpassword")

    def test_vista_jugar_inicializa_partida_y_no_revela_respuestas(self):
        url = reverse("nave:jugar", args=[self.actividad.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # Verificar que el payload en contexto no contenga el tipo ni la solución
        reqs_json = response.context["requerimientos_json"]
        self.assertNotIn('"tipo":', reqs_json)
        self.assertNotIn('"explicacion":', reqs_json)

        anom_json = response.context["anomalias_json"]
        self.assertNotIn('"es_correcta":', anom_json)

    def test_clasificar_endpoint(self):
        # Iniciar primero
        self.client.get(reverse("nave:jugar", args=[self.actividad.id]))

        url = reverse("nave:clasificar", args=[self.actividad.id])
        payload = {"tipo_laser": "RF", "requerimiento_id": self.req.id}
        res = self.client.post(url, data=json.dumps(payload), content_type="application/json")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["ok"])
        self.assertTrue(data["correcto"])
        self.assertEqual(data["tipo_correcto"], "RF")
        self.assertEqual(data["estado"]["puntaje"], 150)

    def test_finalizar_endpoint_registra_progreso_y_desbloquea(self):
        # Iniciar
        self.client.get(reverse("nave:jugar", args=[self.actividad.id]))

        # Simular aciertos que den XP alto
        session = self.client.session
        partidas = session.get("nave_partidas", {})
        partidas[str(self.actividad.id)]["puntaje"] = 8000
        partidas[str(self.actividad.id)]["aciertos_rf"] = 5
        session["nave_partidas"] = partidas
        session.save()

        url = reverse("nave:finalizar", args=[self.actividad.id])
        payload = {"requerimientos_generados": {str(self.req.id): 5}}
        res = self.client.post(url, data=json.dumps(payload), content_type="application/json")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["ok"])
        self.assertGreaterEqual(data["xp"], 70)
        self.assertTrue(data["siguiente_desbloqueada"])

        # Verificar en base de datos
        prog = ProgresoActividad.objects.get(actividad=self.actividad, usuario=self.perfil)
        self.assertEqual(prog.estado, "completado")
        self.assertEqual(prog.puntaje, data["xp"])

        sig_prog = ProgresoActividad.objects.get(actividad=self.siguiente_actividad, usuario=self.perfil)
        self.assertEqual(sig_prog.estado, "disponible")
