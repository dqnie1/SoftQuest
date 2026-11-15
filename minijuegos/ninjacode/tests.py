from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from contenido.models import Actividad, Mundo, ProgresoActividad, Temario
from login.models import Usuario
from minijuegos.ninjacode.models import NinjaCode, RequisitoNinja, TipoRequisitoNinja
from minijuegos.ninjacode.operaciones.OperacionesNinjaCode import OperacionesNinjaCode


class OperacionesNinjaCodeTests(TestCase):
    def setUp(self):
        self.ops = OperacionesNinjaCode()
        mundo = Mundo.objects.create(nombre='Requerimientos', orden=1)
        temario = Temario.objects.create(mundo=mundo, nombre='RF y RNF', orden=1)
        self.actividad = Actividad.objects.create(
            temario=temario, tipo='ninjacode', titulo='NinjaCode', orden=1, puntos_max=100,
        )
        self.juego = NinjaCode.objects.create(actividad=self.actividad)
        self.rf = RequisitoNinja.objects.create(
            ninjacode=self.juego, texto='Iniciar sesión', tipo=TipoRequisitoNinja.FUNCIONAL,
        )
        self.rnf = RequisitoNinja.objects.create(
            ninjacode=self.juego, texto='Respuesta menor a 2s', tipo=TipoRequisitoNinja.NO_FUNCIONAL,
        )

    def test_corte_segun_nivel(self):
        self.assertTrue(self.ops.es_corte_correcto('FUNCIONAL', 1))
        self.assertFalse(self.ops.es_corte_correcto('NO_FUNCIONAL', 1))
        self.assertTrue(self.ops.es_corte_correcto('NO_FUNCIONAL', 2))
        self.assertFalse(self.ops.es_corte_correcto('FUNCIONAL', 2))

    def test_puntaje_25_y_tope_100(self):
        self.assertEqual(self.ops.calcular_puntaje(1), 25)
        self.assertEqual(self.ops.calcular_puntaje(4), 100)
        self.assertEqual(self.ops.calcular_puntaje(8), 100)
        self.assertEqual(self.ops.calcular_puntaje(0), 0)

    def test_evaluar_completa_ambos_niveles(self):
        requisitos = self.ops.cargar_requisitos(self.juego)
        resultado = self.ops.evaluar_partida(
            requisitos,
            [
                {'id': self.rf.id, 'nivel': 1},
                {'id': self.rnf.id, 'nivel': 2},
            ],
            2,
            100,
        )
        self.assertTrue(resultado['completado'])
        self.assertEqual(resultado['puntaje'], 50)
        self.assertEqual(resultado['aciertos'], 2)

    def test_tres_errores_no_completa(self):
        requisitos = self.ops.cargar_requisitos(self.juego)
        cortes = [{'id': self.rnf.id, 'nivel': 1}] * 3
        resultado = self.ops.evaluar_partida(requisitos, cortes, 2, 100)
        self.assertFalse(resultado['completado'])
        self.assertEqual(resultado['puntaje'], 0)


class NinjaCodeViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='ninja', password='password123')
        self.usuario = Usuario.objects.create(nombre='Ninja', email='n@test.com', cuenta=self.user)
        self.mundo = Mundo.objects.create(nombre='Requerimientos', orden=1)
        self.temario = Temario.objects.create(mundo=self.mundo, nombre='RF', orden=1)
        self.actividad = Actividad.objects.create(
            temario=self.temario, tipo='ninjacode', titulo='NinjaCode', orden=1, puntos_max=100,
        )
        self.juego = NinjaCode.objects.create(actividad=self.actividad)
        self.rf = RequisitoNinja.objects.create(
            ninjacode=self.juego, texto='Registrar usuario', tipo=TipoRequisitoNinja.FUNCIONAL,
        )
        self.rnf = RequisitoNinja.objects.create(
            ninjacode=self.juego, texto='Disponibilidad 99.9%', tipo=TipoRequisitoNinja.NO_FUNCIONAL,
        )
        self.client.force_login(self.user)

    def test_carga_frutas_en_plantilla(self):
        respuesta = self.client.get(reverse('ninjacode:jugar', args=[self.actividad.id]))
        self.assertContains(respuesta, 'Registrar usuario')
        self.assertContains(respuesta, 'FUNCIONAL')
        self.assertContains(respuesta, 'Corta únicamente las frutas que representen Requisitos Funcionales')

    def test_error_si_faltan_frutas(self):
        vacia = Actividad.objects.create(
            temario=self.temario, tipo='ninjacode', titulo='Vacío', orden=2, puntos_max=100,
        )
        respuesta = self.client.get(reverse('ninjacode:jugar', args=[vacia.id]))
        self.assertContains(respuesta, 'Error al cargar NinjaCode')

    def test_guardar_progreso_completa(self):
        respuesta = self.client.post(
            reverse('ninjacode:guardar_progreso', args=[self.actividad.id]),
            data={
                'cortes': [
                    {'id': self.rf.id, 'nivel': 1},
                    {'id': self.rnf.id, 'nivel': 2},
                ],
                'niveles_completados': 2,
            },
            content_type='application/json',
        )
        self.assertEqual(respuesta.json()['guardado'], True)
        progreso = ProgresoActividad.objects.get(usuario=self.usuario, actividad=self.actividad)
        self.assertEqual(progreso.estado, 'completado')
        self.assertEqual(progreso.puntaje, 50)

    def test_game_over_no_completa(self):
        respuesta = self.client.post(
            reverse('ninjacode:guardar_progreso', args=[self.actividad.id]),
            data={
                'cortes': [
                    {'id': self.rnf.id, 'nivel': 1},
                    {'id': self.rnf.id, 'nivel': 1},
                    {'id': self.rnf.id, 'nivel': 1},
                ],
                'niveles_completados': 2,
            },
            content_type='application/json',
        )
        self.assertFalse(respuesta.json()['guardado'])
        self.assertFalse(ProgresoActividad.objects.filter(actividad=self.actividad).exists())

    def test_corte_id_ajeno_es_invalido(self):
        respuesta = self.client.post(
            reverse('ninjacode:guardar_progreso', args=[self.actividad.id]),
            data={'cortes': [{'id': 999999, 'nivel': 1}], 'niveles_completados': 2},
            content_type='application/json',
        )
        self.assertEqual(respuesta.status_code, 400)
        self.assertFalse(ProgresoActividad.objects.filter(actividad=self.actividad).exists())
