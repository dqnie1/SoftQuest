import json
from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from contenido.models import Mundo, Temario, Actividad
from login.models import Usuario
from .model.ModeloAhorcado import AhorcadoJuego, PalabraAhorcado, PistaAhorcado, ModeloAhorcado
from .model.ProgresoActividad import ProgresoActividad
from .operaciones.OperacionesAhorcado import (
    OperacionesAhorcado,
    actividad_desbloqueada,
    calcular_puntaje,
    normalizar_letra,
    normalizar_palabra,
)


class OperacionesAhorcadoTestCase(TestCase):
    """
    Pruebas unitarias para OperacionesAhorcado en minijuegos/ahorcado.
    """

    def setUp(self):
        self.auth_user = User.objects.create_user(
            username='jugador_test',
            email='jugador@softquest.edu',
            password='password123'
        )
        self.usuario = Usuario.objects.create(
            cuenta=self.auth_user,
            nombre='Jugador de Prueba',
            email='jugador@softquest.edu'
        )

        self.mundo = Mundo.objects.create(nombre='Mundo 1: Fundamentos', orden=1)
        self.temario = Temario.objects.create(mundo=self.mundo, nombre='Unidad 1', orden=1)

        self.actividad_previa = Actividad.objects.create(
            temario=self.temario,
            tipo='trivia',
            titulo='Trivia Introductoria',
            orden=1,
            puntos_max=100
        )

        self.actividad_ahorcado = Actividad.objects.create(
            temario=self.temario,
            tipo='ahorcado',
            titulo='Ahorcado: Programación',
            orden=2,
            puntos_max=100
        )
        self.juego = AhorcadoJuego.objects.create(actividad=self.actividad_ahorcado)

        self.palabra_obj = PalabraAhorcado.objects.create(
            ahorcado=self.juego,
            palabra='PYTHON',
            pista_inicial='Lenguaje de programación de alto nivel.',
            letras_expuestas=1
        )
        self.pista1 = PistaAhorcado.objects.create(
            palabra=self.palabra_obj,
            texto='Creado por Guido van Rossum.',
            orden=1
        )
        self.pista2 = PistaAhorcado.objects.create(
            palabra=self.palabra_obj,
            texto='Usa indentación para delimitar bloques.',
            orden=2
        )
        self.pista3 = PistaAhorcado.objects.create(
            palabra=self.palabra_obj,
            texto='Su nombre proviene de Monty Python.',
            orden=3
        )

        self.client = Client()
        self.client.force_login(self.auth_user)
        self.ops = OperacionesAhorcado()

    def test_normalizacion_de_letras_y_palabras(self):
        self.assertEqual(normalizar_letra('a'), 'A')
        self.assertEqual(normalizar_letra('á'), 'A')
        self.assertEqual(normalizar_letra('É'), 'E')
        self.assertEqual(normalizar_letra('ñ'), 'Ñ')
        self.assertEqual(normalizar_letra('Ñ'), 'Ñ')

        self.assertEqual(normalizar_palabra('PROGRAMACIÓN'), 'PROGRAMACION')
        self.assertEqual(normalizar_palabra('diseño'), 'DISEÑO')

    def test_calculo_puntaje(self):
        self.assertEqual(calcular_puntaje(100, fallos_cometidos=0, pistas_usadas=0), 100)
        self.assertEqual(calcular_puntaje(100, fallos_cometidos=1, pistas_usadas=1), 85)
        self.assertEqual(calcular_puntaje(100, fallos_cometidos=6, pistas_usadas=3, gano=False), 25)
        self.assertEqual(calcular_puntaje(50, fallos_cometidos=6, pistas_usadas=3, gano=False), 0)

    def test_flujo_normal_victoria_y_escritura_progreso(self):
        res_inicio = self.ops.iniciarPartida(self.usuario, self.actividad_ahorcado.id)
        self.assertTrue(res_inicio['ok'])
        self.assertEqual(res_inicio['fallos_restantes'], 6)
        self.assertEqual(res_inicio['pistas_restantes'], 3)
        self.assertEqual(res_inicio['pista_inicial'], 'Lenguaje de programación de alto nivel.')

        progreso = ProgresoActividad.objects.filter(
            usuario_id=self.usuario.id,
            actividad_id=self.actividad_ahorcado.id
        ).first()
        self.assertIsNotNone(progreso)
        self.assertEqual(progreso.estado, 'en_progreso')
        self.assertEqual(progreso.intentos, 1)

        res_letra_y = self.ops.validar_letra(self.usuario, self.actividad_ahorcado.id, 'Y')
        self.assertTrue(res_letra_y['ok'])
        self.assertTrue(res_letra_y['acierto'])
        self.assertFalse(res_letra_y['completada'])

        for l in ['P', 'T', 'H', 'O', 'N']:
            res_fin = self.ops.validar_letra(self.usuario, self.actividad_ahorcado.id, l)

        self.assertTrue(res_fin['ok'])
        self.assertTrue(res_fin['completada'])
        self.assertTrue(res_fin['gano'])
        self.assertEqual(res_fin['palabra_revelada'], 'PYTHON')

        progreso.refresh_from_db()
        self.assertEqual(progreso.estado, 'completado')
        self.assertEqual(progreso.puntaje, 100)
        self.assertIsNotNone(progreso.fecha_completado)

    def test_flujo_1_1_letra_incorrecta_y_repetida(self):
        self.ops.iniciarPartida(self.usuario, self.actividad_ahorcado.id)

        res_z = self.ops.validar_letra(self.usuario, self.actividad_ahorcado.id, 'Z')
        self.assertTrue(res_z['ok'])
        self.assertFalse(res_z['acierto'])
        self.assertEqual(res_z['fallos_restantes'], 5)

        res_z_rep = self.ops.validar_letra(self.usuario, self.actividad_ahorcado.id, 'Z')
        self.assertTrue(res_z_rep['ok'])
        self.assertTrue(res_z_rep.get('repetida', False))
        self.assertEqual(res_z_rep['fallos_restantes'], 5)

    def test_flujo_1_2_pedir_pista_disponible(self):
        self.ops.iniciarPartida(self.usuario, self.actividad_ahorcado.id)

        res_p1 = self.ops.solicitar_pista(self.usuario, self.actividad_ahorcado.id)
        self.assertTrue(res_p1['ok'])
        self.assertEqual(res_p1['pista'], 'Creado por Guido van Rossum.')
        self.assertEqual(res_p1['pistas_restantes'], 2)

        res_p2 = self.ops.solicitar_pista(self.usuario, self.actividad_ahorcado.id)
        self.assertTrue(res_p2['ok'])
        self.assertEqual(res_p2['pista'], 'Usa indentación para delimitar bloques.')
        self.assertEqual(res_p2['pistas_restantes'], 1)

    def test_flujo_1_3_ciclo_de_pistas_al_agotar_las_3(self):
        """
        Al solicitar más de 3 pistas, cicla volviendo a mostrar la primera
        ya que solo se ve la última pista solicitada en la tarjeta.
        """
        self.ops.iniciarPartida(self.usuario, self.actividad_ahorcado.id)

        # Desbloquear las 3 pistas
        p1 = self.ops.solicitar_pista(self.usuario, self.actividad_ahorcado.id)
        self.assertEqual(p1['pista'], 'Creado por Guido van Rossum.')
        p2 = self.ops.solicitar_pista(self.usuario, self.actividad_ahorcado.id)
        self.assertEqual(p2['pista'], 'Usa indentación para delimitar bloques.')
        p3 = self.ops.solicitar_pista(self.usuario, self.actividad_ahorcado.id)
        self.assertEqual(p3['pista'], 'Su nombre proviene de Monty Python.')

        # 4ª solicitud: vuelve a mostrar la primera
        res_p4 = self.ops.solicitar_pista(self.usuario, self.actividad_ahorcado.id)
        self.assertTrue(res_p4['ok'])
        self.assertEqual(res_p4['pistas_restantes'], 0)
        self.assertEqual(res_p4['pista'], 'Creado por Guido van Rossum.')
        self.assertTrue(res_p4['ciclando'])

    def test_flujo_1_4_agotamiento_de_6_fallos_derrota(self):
        self.ops.iniciarPartida(self.usuario, self.actividad_ahorcado.id)

        letras_erroneas = ['A', 'B', 'C', 'D', 'E', 'F']
        res = None
        for l in letras_erroneas:
            res = self.ops.validar_letra(self.usuario, self.actividad_ahorcado.id, l)

        self.assertTrue(res['ok'])
        self.assertTrue(res['completada'])
        self.assertTrue(res['perdio'])
        self.assertEqual(res['fallos_restantes'], 0)
        self.assertEqual(res['palabra_revelada'], 'PYTHON')

        progreso = ProgresoActividad.objects.get(
            usuario_id=self.usuario.id,
            actividad_id=self.actividad_ahorcado.id
        )
        self.assertEqual(progreso.estado, 'no_completado')
        self.assertEqual(progreso.puntaje, 40)
        self.assertIsNotNone(progreso.fecha_completado)

    def test_flujo_1_5_abandonar_actividad(self):
        self.ops.iniciarPartida(self.usuario, self.actividad_ahorcado.id)

        res_abandono = self.ops.abandonar_actividad(self.usuario, self.actividad_ahorcado.id)
        self.assertTrue(res_abandono['ok'])
        self.assertIn('redirect_url', res_abandono)

        progreso = ProgresoActividad.objects.get(
            usuario_id=self.usuario.id,
            actividad_id=self.actividad_ahorcado.id
        )
        self.assertEqual(progreso.estado, 'no_completado')
        self.assertIsNotNone(progreso.fecha_completado)

    def test_excepcion_1_0_e1_error_de_carga_sin_palabras(self):
        act_vacia = Actividad.objects.create(
            temario=self.temario,
            tipo='ahorcado',
            titulo='Ahorcado Vacío',
            orden=99,
            puntos_max=100
        )
        AhorcadoJuego.objects.create(actividad=act_vacia)

        contenido = self.ops.obtenerContenido(self.usuario, act_vacia.id)
        self.assertIsNone(contenido)

        existe_progreso = ProgresoActividad.objects.filter(
            usuario_id=self.usuario.id,
            actividad_id=act_vacia.id
        ).exists()
        self.assertFalse(existe_progreso)

    def test_precondicion_pre_2_actividad_desbloqueada(self):
        self.assertFalse(actividad_desbloqueada(self.usuario, self.actividad_ahorcado))

        ProgresoActividad.objects.create(
            usuario=self.usuario,
            actividad=self.actividad_previa,
            estado='completado',
            puntaje=100,
            intentos=1
        )

        self.assertTrue(actividad_desbloqueada(self.usuario, self.actividad_ahorcado))

    def test_endpoints_http_vistas(self):
        ProgresoActividad.objects.create(
            usuario=self.usuario,
            actividad=self.actividad_previa,
            estado='completado',
            puntaje=100
        )

        response_get = self.client.get(f'/ahorcado/{self.actividad_ahorcado.id}/')
        self.assertEqual(response_get.status_code, 200)
        self.assertContains(response_get, 'Ahorcado: Programación')

        response_iniciar = self.client.post(
            '/ahorcado/iniciar',
            data=json.dumps({'actividad_id': self.actividad_ahorcado.id}),
            content_type='application/json'
        )
        self.assertEqual(response_iniciar.status_code, 200)
        data_inicio = response_iniciar.json()
        self.assertTrue(data_inicio['ok'])

        response_letra = self.client.post(
            '/ahorcado/letra',
            data=json.dumps({'actividad_id': self.actividad_ahorcado.id, 'letra': 'P'}),
            content_type='application/json'
        )
        self.assertEqual(response_letra.status_code, 200)
        data_letra = response_letra.json()
        self.assertTrue(data_letra['ok'])

        response_pista = self.client.post(
            '/ahorcado/pista',
            data=json.dumps({'actividad_id': self.actividad_ahorcado.id}),
            content_type='application/json'
        )
        self.assertEqual(response_pista.status_code, 200)
        data_pista = response_pista.json()
        self.assertTrue(data_pista['ok'])

        response_abandonar = self.client.post(
            '/ahorcado/abandonar',
            data=json.dumps({'actividad_id': self.actividad_ahorcado.id}),
            content_type='application/json'
        )
        self.assertEqual(response_abandonar.status_code, 200)
        data_abandono = response_abandonar.json()
        self.assertTrue(data_abandono['ok'])
