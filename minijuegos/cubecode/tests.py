from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from contenido.models import Actividad, Mundo, ProgresoActividad, Temario
from login.models import Usuario
from minijuegos.cubecode.models import (
    BloqueCubeCode,
    CubeCode,
    EjercicioCubeCode,
    NivelCubeCode,
)
from minijuegos.cubecode.operaciones.OperacionesCubeCode import OperacionesCubeCode


class OperacionesCubeCodeTests(TestCase):
    def setUp(self):
        self.ops = OperacionesCubeCode()
        self.mundo = Mundo.objects.create(nombre='Programación', orden=1)
        self.temario = Temario.objects.create(mundo=self.mundo, nombre='Básica', orden=1)
        self.actividad = Actividad.objects.create(
            temario=self.temario,
            tipo='cubecode',
            titulo='CubeCode',
            orden=1,
            puntos_max=100,
        )
        self.cubecode = CubeCode.objects.create(actividad=self.actividad)
        self.nivel = NivelCubeCode.objects.create(cubecode=self.cubecode, numero=1, nombre='Fundamentos')
        self.ejercicio = EjercicioCubeCode.objects.create(
            nivel=self.nivel,
            numero=1,
            titulo='Promedio',
            objetivo='Calcular el promedio.',
        )
        self.primero = BloqueCubeCode.objects.create(
            ejercicio=self.ejercicio, texto='a = 1', orden_solucion=1, pista='Primero',
        )
        self.segundo = BloqueCubeCode.objects.create(
            ejercicio=self.ejercicio, texto='print(a)', orden_solucion=2, pista='Después',
        )
        self.senuelo = BloqueCubeCode.objects.create(
            ejercicio=self.ejercicio, texto='a = 0', orden_solucion=None, pista='',
        )

    def test_calcular_puntaje_sobre_100(self):
        self.assertEqual(self.ops.calcular_puntaje(0, 12), 0)
        self.assertEqual(self.ops.calcular_puntaje(1, 12), 8)
        self.assertEqual(self.ops.calcular_puntaje(4, 12), 33)
        self.assertEqual(self.ops.calcular_puntaje(8, 12), 66)
        self.assertEqual(self.ops.calcular_puntaje(12, 12), 100)
        self.assertEqual(self.ops.calcular_puntaje(13, 12), 100)
        self.assertEqual(self.ops.calcular_puntaje('no', 12), 0)

    def test_validar_solucion(self):
        correcto = [self.primero.id, self.segundo.id]
        self.assertTrue(self.ops.validar_solucion(self.ejercicio, correcto))
        self.assertFalse(self.ops.validar_solucion(self.ejercicio, [self.segundo.id, self.primero.id]))
        self.assertFalse(self.ops.validar_solucion(self.ejercicio, correcto + [self.senuelo.id]))
        self.assertFalse(self.ops.validar_solucion(self.ejercicio, [self.primero.id]))
        self.assertFalse(self.ops.validar_solucion(self.ejercicio, ['x']))

    def test_serializar_no_revela_la_solucion(self):
        datos = self.ops.serializar_ejercicio(self.ejercicio, [], 0)
        self.assertEqual(datos['titulo'], 'Promedio')
        self.assertEqual(len(datos['bloques']), 3)
        self.assertNotIn('pistas', datos)
        self.assertFalse(any('orden' in bloque for bloque in datos['bloques']))


class CubeCodeViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='jugador', password='password123')
        self.usuario = Usuario.objects.create(
            nombre='Jugador',
            email='jugador@test.com',
            cuenta=self.user,
        )
        self.mundo = Mundo.objects.create(nombre='Programación', orden=1)
        self.temario = Temario.objects.create(mundo=self.mundo, nombre='Básica', orden=1)
        self.actividad = Actividad.objects.create(
            temario=self.temario,
            tipo='cubecode',
            titulo='CubeCode',
            orden=1,
            puntos_max=100,
        )
        self.cubecode = CubeCode.objects.create(actividad=self.actividad)
        self.nivel_1 = NivelCubeCode.objects.create(cubecode=self.cubecode, numero=1, nombre='Fundamentos')
        self.nivel_2 = NivelCubeCode.objects.create(cubecode=self.cubecode, numero=2, nombre='Bucles')
        self.ejercicio_1 = self._ejercicio(self.nivel_1, 1, 'Inicio')
        self.ejercicio_2 = self._ejercicio(self.nivel_2, 1, 'Cierre')
        self.client.force_login(self.user)

    def _ejercicio(self, nivel, numero, titulo):
        ejercicio = EjercicioCubeCode.objects.create(
            nivel=nivel,
            numero=numero,
            titulo=titulo,
            objetivo='Armar el fragmento.',
        )
        BloqueCubeCode.objects.create(ejercicio=ejercicio, texto='valor = 1', orden_solucion=1, pista='Asigna')
        BloqueCubeCode.objects.create(ejercicio=ejercicio, texto='print(valor)', orden_solucion=2, pista='Muestra')
        BloqueCubeCode.objects.create(ejercicio=ejercicio, texto='valor = 0', orden_solucion=None)
        return ejercicio

    def _ids(self, ejercicio):
        return list(
            ejercicio.bloques.exclude(orden_solucion__isnull=True)
            .order_by('orden_solucion')
            .values_list('id', flat=True)
        )

    def test_jugar_y_temario(self):
        respuesta = self.client.get(reverse('cubecode:jugar', args=[self.actividad.id]))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'Inicio')
        temario = self.client.get(reverse('temario_mundo', args=[self.mundo.id]))
        self.assertContains(temario, f'/cubecode/{self.actividad.id}/')

    def test_comprobar_incorrecto_no_suma(self):
        respuesta = self.client.post(
            reverse('cubecode:comprobar', args=[self.actividad.id]),
            data='{"ejercicio_id": %d, "bloques": [1]}' % self.ejercicio_1.id,
            content_type='application/json',
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(respuesta.json()['correcto'])
        self.assertFalse(ProgresoActividad.objects.filter(estado='completado').exists())

    def test_completar_niveles_guarda_100(self):
        primero = self.client.post(
            reverse('cubecode:comprobar', args=[self.actividad.id]),
            data={'ejercicio_id': self.ejercicio_1.id, 'bloques': self._ids(self.ejercicio_1)},
            content_type='application/json',
        )
        self.assertEqual(primero.json()['accion'], 'nivel')
        self.assertEqual(primero.json()['score'], 50)

        segundo = self.client.post(
            reverse('cubecode:comprobar', args=[self.actividad.id]),
            data={'ejercicio_id': self.ejercicio_2.id, 'bloques': self._ids(self.ejercicio_2)},
            content_type='application/json',
        )
        self.assertEqual(segundo.json()['accion'], 'fin')
        self.assertEqual(segundo.json()['resumen_final']['score'], 100)
        progreso = ProgresoActividad.objects.get(actividad=self.actividad, usuario=self.usuario)
        self.assertEqual(progreso.estado, 'completado')
        self.assertEqual(progreso.puntaje, 100)

    def test_salir_conserva_el_avance(self):
        self.client.post(
            reverse('cubecode:comprobar', args=[self.actividad.id]),
            data={'ejercicio_id': self.ejercicio_1.id, 'bloques': self._ids(self.ejercicio_1)},
            content_type='application/json',
        )
        salida = self.client.post(reverse('cubecode:salir', args=[self.actividad.id]))
        self.assertRedirects(salida, reverse('cubecode:salida', args=[self.actividad.id]))
        pagina = self.client.get(reverse('cubecode:salida', args=[self.actividad.id]))
        self.assertContains(pagina, 'no se considera completado')
        self.assertContains(pagina, '0/1 ejercicios')
        juego = self.client.get(reverse('cubecode:jugar', args=[self.actividad.id]))
        self.assertContains(juego, 'Cierre')

    def test_sin_bloques_muestra_el_error(self):
        otra = Actividad.objects.create(
            temario=self.temario,
            tipo='cubecode',
            titulo='Vacío',
            orden=2,
            puntos_max=100,
        )
        respuesta = self.client.get(reverse('cubecode:jugar', args=[otra.id]))
        self.assertContains(respuesta, 'No se pudo cargar el juego')
