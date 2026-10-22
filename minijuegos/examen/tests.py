from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
import json

from contenido.models import Mundo, Temario, Actividad, ProgresoActividad, ProgresoUsuario, Insignia, InsigniaUsuario
from login.models import Usuario
from minijuegos.trivia.models import Trivia, Pregunta, Respuesta
from minijuegos.match.models import MatchJuego, Concepto
from minijuegos.examen.models import IntentoExamen
from minijuegos.examen.operaciones.OperacionesExamen import OperacionesExamen, ExcepcionCargaExamen


class ExamenTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.auth_user = User.objects.create_user(
            username='estudiante_test',
            email='estudiante@uaz.edu.mx',
            password='password123'
        )
        self.usuario = Usuario.objects.create(
            cuenta=self.auth_user,
            nombre='Estudiante Test',
            email='estudiante@uaz.edu.mx'
        )

        # Crear mundos
        self.mundo_1 = Mundo.objects.create(nombre='Mundo 1 Test', orden=1)
        self.mundo_2 = Mundo.objects.create(nombre='Mundo 2 Test', orden=2)

        # Progreso inicial
        self.progreso_usuario = ProgresoUsuario.objects.create(
            usuario=self.usuario,
            mundo_actual=self.mundo_1
        )

        # Temario y actividades para Mundo 1
        self.temario_1 = Temario.objects.create(mundo=self.mundo_1, nombre='Unidad 1 Test', orden=1)

        self.act_trivia = Actividad.objects.create(
            temario=self.temario_1,
            tipo='trivia',
            titulo='Trivia 1',
            orden=1,
            puntos_max=100
        )
        self.act_match = Actividad.objects.create(
            temario=self.temario_1,
            tipo='match_juego',
            titulo='Match 1',
            orden=2,
            puntos_max=100
        )

        # Contenido de Trivia
        self.trivia_obj = Trivia.objects.create(actividad=self.act_trivia)
        self.pregunta_1 = Pregunta.objects.create(trivia=self.trivia_obj, texto='¿Qué es software?')
        self.resp_1_corr = Respuesta.objects.create(pregunta=self.pregunta_1, texto='Conjunto de programas y datos', es_correcta=True)
        self.resp_1_inc = Respuesta.objects.create(pregunta=self.pregunta_1, texto='Hardware físico', es_correcta=False)

        # Contenido de Match
        self.match_obj = MatchJuego.objects.create(actividad=self.act_match)
        self.concepto_1 = Concepto.objects.create(match=self.match_obj, termino='Bug', definicion='Defecto de software')

        # Insignia para Mundo 1
        self.insignia_1 = Insignia.objects.create(
            mundo=self.mundo_1,
            nombre='Insignia Mundo 1',
            descripcion='Premio por aprobar Mundo 1'
        )

    def test_verificar_habilitado_rn39(self):
        """RN-39: Examen solo habilitado si todas las actividades evaluables están completadas."""
        ops = OperacionesExamen()
        # Inicialmente ninguna actividad completada
        self.assertFalse(ops.verificar_habilitado(self.usuario, self.mundo_1))

        # Completar solo una actividad
        ProgresoActividad.objects.create(
            usuario=self.usuario,
            actividad=self.act_trivia,
            estado='completado',
            puntaje=100
        )
        self.assertFalse(ops.verificar_habilitado(self.usuario, self.mundo_1))

        # Completar la segunda actividad
        ProgresoActividad.objects.create(
            usuario=self.usuario,
            actividad=self.act_match,
            estado='completado',
            puntaje=100
        )
        self.assertTrue(ops.verificar_habilitado(self.usuario, self.mundo_1))

    def test_generar_examen_rn40_rn41(self):
        """RN-40 y RN-41: El examen genera bloques con preguntas de trivia y conceptos en orden aleatorio."""
        ops = OperacionesExamen()
        data = ops.generar_examen(self.mundo_1)

        self.assertEqual(data['total_bloques'], 1)
        bloque = data['bloques'][0]
        self.assertEqual(bloque['nombre_temario'], 'Unidad 1 Test')
        self.assertEqual(len(bloque['preguntas']), 1)
        self.assertEqual(len(bloque['conceptos']), 1)
        self.assertEqual(len(bloque['definiciones']), 1)

        # Las preguntas enviadas al cliente no deben tener es_correcta
        self.assertNotIn('es_correcta', bloque['preguntas'][0]['respuestas'][0])

        # Claves del servidor sí contienen la respuesta correcta
        clave_trivia = data['claves'][f"trivia_{self.pregunta_1.id}"]
        self.assertEqual(clave_trivia['respuesta_correcta_id'], self.resp_1_corr.id)

    def test_evaluar_y_aprobar_rn45_rn46_rn47_rn49(self):
        """Aprobar examen (>=70%): actualiza progreso mundo, otorga insignia y registra intento."""
        ops = OperacionesExamen()
        examen_data = ops.generar_examen(self.mundo_1)

        # Responder correctamente ambos reactivos
        respuestas = {
            f"trivia_{self.pregunta_1.id}": self.resp_1_corr.id,
            f"concepto_{self.concepto_1.id}": self.concepto_1.id
        }

        resultado = ops.evaluar_y_registrar(
            usuario=self.usuario,
            mundo=self.mundo_1,
            examen_session_data=examen_data,
            respuestas_usuario=respuestas,
            tiempo_empleado=120
        )

        self.assertTrue(resultado['aprobado'])
        self.assertEqual(resultado['calificacion'], 100.0)
        self.assertEqual(resultado['total_aciertos'], 2)

        # Intento registrado (RN-51)
        self.assertEqual(IntentoExamen.objects.count(), 1)
        intento = IntentoExamen.objects.first()
        self.assertTrue(intento.aprobado)
        self.assertEqual(intento.tiempo_empleado_segundos, 120)

        # Mundo desbloqueado
        self.progreso_usuario.refresh_from_db()
        self.assertEqual(self.progreso_usuario.mundo_actual.id, self.mundo_2.id)

    def test_evaluar_y_reprobar_rn46_rn50(self):
        """Reprobar examen (<70%): no otorga insignia y el mundo siguiente sigue bloqueado."""
        ops = OperacionesExamen()
        examen_data = ops.generar_examen(self.mundo_1)

        # Responder incorrectamente
        respuestas = {
            f"trivia_{self.pregunta_1.id}": self.resp_1_inc.id,
            f"concepto_{self.concepto_1.id}": 999999  # incorrecto
        }

        resultado = ops.evaluar_y_registrar(
            usuario=self.usuario,
            mundo=self.mundo_1,
            examen_session_data=examen_data,
            respuestas_usuario=respuestas,
            tiempo_empleado=150
        )

        self.assertFalse(resultado['aprobado'])
        self.assertEqual(resultado['calificacion'], 0.0)

        # Intento registrado como no aprobado (RN-51)
        intento = IntentoExamen.objects.first()
        self.assertFalse(intento.aprobado)

        # No se otorga insignia (RN-49, RN-50)
        self.assertFalse(InsigniaUsuario.objects.filter(usuario=self.usuario, insignia=self.insignia_1).exists())

        # El mundo siguiente NO se desbloquea (RN-50)
        self.progreso_usuario.refresh_from_db()
        self.assertEqual(self.progreso_usuario.mundo_actual.id, self.mundo_1.id)

    def test_flujo_vistas_completo(self):
        """Prueba end-to-end de las vistas del examen vía HTTP."""
        self.client.login(username='estudiante_test', password='password123')

        # Completar actividades para habilitar examen (RN-39)
        ProgresoActividad.objects.create(usuario=self.usuario, actividad=self.act_trivia, estado='completado', puntaje=100)
        ProgresoActividad.objects.create(usuario=self.usuario, actividad=self.act_match, estado='completado', puntaje=100)

        # 1. Vista examen_inicio
        url_inicio = reverse('examen:examen_inicio', kwargs={'mundo_id': self.mundo_1.id})
        response = self.client.get(url_inicio)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Examen Final')

        # 2. Vista examen_presentar
        url_presentar = reverse('examen:examen_presentar', kwargs={'mundo_id': self.mundo_1.id})
        response = self.client.get(url_presentar)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Bloque 1')

        # 3. Vista examen_calificar
        url_calificar = reverse('examen:examen_calificar', kwargs={'mundo_id': self.mundo_1.id})
        payload = {
            'respuestas': {
                f"trivia_{self.pregunta_1.id}": self.resp_1_corr.id,
                f"concepto_{self.concepto_1.id}": self.concepto_1.id
            },
            'tiempo_empleado': 95
        }
        response = self.client.post(
            url_calificar,
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('redirect_url', data)

        # 4. Vista examen_resultado
        response_res = self.client.get(data['redirect_url'])
        self.assertEqual(response_res.status_code, 200)
        self.assertContains(response_res, '¡Felicidades, examen aprobado!')
        self.assertContains(response_res, '100')
