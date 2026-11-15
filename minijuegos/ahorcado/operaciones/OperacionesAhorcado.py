import unicodedata
from django.db import DatabaseError
from django.urls import reverse
from django.utils import timezone

from contenido.models import Actividad, ProgresoUsuario
from ..model.ModeloAhorcado import AhorcadoJuego, ModeloAhorcado, PistaAhorcado
from ..model.ProgresoActividad import ProgresoActividad


def normalizar_letra(letra: str) -> str:
    """
    Normaliza una letra: la convierte a mayúscula y remueve acentos (ej. Á -> A).
    Conserva la letra 'Ñ' como un carácter independiente en español.
    """
    if not letra:
        return ''
    letra = letra.strip().upper()
    if not letra:
        return ''
    ch = letra[0]
    if ch == 'Ñ':
        return 'Ñ'
    nfkd = unicodedata.normalize('NFKD', ch)
    sin_acento = ''.join(c for c in nfkd if unicodedata.category(c) != 'Mn')
    return sin_acento


def normalizar_palabra(palabra: str) -> str:
    """
    Normaliza una palabra completa ignorando tildes pero conservando 'Ñ' y espacios.
    """
    if not palabra:
        return ''
    res = []
    for ch in palabra.upper():
        if ch == 'Ñ':
            res.append('Ñ')
        elif ch.isspace() or ch in '-_':
            res.append(ch)
        else:
            nfkd = unicodedata.normalize('NFKD', ch)
            res.append(''.join(c for c in nfkd if unicodedata.category(c) != 'Mn'))
    return ''.join(res)


def calcular_puntaje(puntos_max: int, fallos_cometidos: int, pistas_usadas: int, gano: bool = True) -> int:
    """
    POST-02: Calificación obtenida calculada por una función aislada y configurable.
    Tope: ACTIVIDAD.puntos_max (100 xp, RN-G01).
    Fórmula: puntos_max base, menos 10 por fallo cometido y 5 por pista única usada (máx 3 pistas penalizadas).
    Mínimo: 0. Si pierde, se aplica la misma función y el estado es 'no_completada'.
    """
    base = puntos_max if (puntos_max is not None and puntos_max > 0) else 100
    pistas_penalizables = min(3, max(0, pistas_usadas))
    penalizacion = (max(0, fallos_cometidos) * 10) + (pistas_penalizables * 5)
    puntaje = max(0, base - penalizacion)
    return min(puntaje, base)


def actividad_desbloqueada(usuario, actividad) -> bool:
    """
    PRE-2: Función aislada que determina si la actividad está desbloqueada.
    """
    if not usuario or not actividad:
        return False

    temario = getattr(actividad, 'temario', None)
    if not temario:
        return False

    progreso_u = ProgresoUsuario.objects.filter(usuario=usuario).first()
    if progreso_u and progreso_u.mundo_actual:
        if temario.mundo.orden > progreso_u.mundo_actual.orden:
            return False

    actividades_previas = Actividad.objects.filter(
        temario=temario,
        orden__lt=actividad.orden
    ).order_by('-orden')

    actividad_previa = actividades_previas.first()
    if not actividad_previa:
        return True

    progreso_prev = ProgresoActividad.objects.filter(
        usuario=usuario,
        actividad=actividad_previa,
        estado__in=['completada', 'completado']
    ).first()

    return progreso_prev is not None


class OperacionesAhorcado:
    """
    Capa de lógica de negocio para el caso de uso CU-07: Jugar Ahorcado.
    La partida en curso vive en la sesión del servidor (request.session).
    """
    _test_sessions = {}

    def __init__(self, request=None):
        self.request = request

    def _session_key(self, actividad_id):
        return f"ahorcado_partida_{actividad_id}"

    def _obtener_partida(self, actividad_id):
        key = self._session_key(actividad_id)
        if self.request and hasattr(self.request, 'session'):
            return self.request.session.get(key)
        return self._test_sessions.get(key)

    def _guardar_partida(self, actividad_id, datos):
        key = self._session_key(actividad_id)
        if self.request and hasattr(self.request, 'session'):
            self.request.session[key] = datos
            self.request.session.modified = True
        else:
            self._test_sessions[key] = datos

    def _limpiar_partida(self, actividad_id):
        key = self._session_key(actividad_id)
        if self.request and hasattr(self.request, 'session'):
            if key in self.request.session:
                del self.request.session[key]
                self.request.session.modified = True
        else:
            self._test_sessions.pop(key, None)

    def _calcular_estado_tablero(self, palabra_original, palabra_normalizada, letras_acertadas):
        tablero = []
        for i, ch_orig in enumerate(palabra_original):
            if ch_orig.isspace():
                tablero.append(' ')
            elif ch_orig in '-_':
                tablero.append(ch_orig)
            else:
                ch_norm = palabra_normalizada[i]
                if ch_norm in letras_acertadas:
                    tablero.append(ch_orig)
                else:
                    tablero.append('_')
        return tablero

    def obtenerContenido(self, usuario, actividad_id):
        """
        # Pasos 1 al 6 del diagrama de secuencia (GET /ahorcado).
        """
        try:
            actividad = Actividad.objects.select_related('temario__mundo').filter(id=actividad_id).first()
            if not actividad:
                return None

            ahorcado_juego = AhorcadoJuego.objects.filter(actividad_id=actividad_id).first()
            if not ahorcado_juego:
                return None

            resultado = ModeloAhorcado.obtenerPalabraActual(actividad_id)
            if not resultado:
                return None

            palabra_obj, pistas = resultado

            url_temario = '/'
            try:
                if actividad.temario and actividad.temario.mundo_id:
                    url_temario = reverse('temario_mundo', args=[actividad.temario.mundo_id])
                else:
                    url_temario = reverse('mapa_mundos')
            except Exception:
                url_temario = '/'

            # Contar total actividades y orden dentro del temario para indicador nivel X de Y
            total_actividades = 1
            nivel_actual = actividad.orden or 1
            if actividad.temario:
                total_actividades = Actividad.objects.filter(temario_id=actividad.temario_id).count() or 1

            return {
                'actividad_id': actividad.id,
                'titulo': actividad.titulo,
                'puntos_max': actividad.puntos_max or 100,
                'tipo': actividad.tipo,
                'url_temario': url_temario,
                'temario_nombre': actividad.temario.nombre if actividad.temario else '',
                'mundo_nombre': actividad.temario.mundo.nombre if actividad.temario and actividad.temario.mundo else '',
                'nivel_actual': nivel_actual,
                'total_actividades': total_actividades,
            }
        except DatabaseError:
            return None
        except Exception:
            return None

    def iniciarPartida(self, usuario, actividad_id):
        """
        # Pasos 9 al 14 del diagrama de secuencia (POST /ahorcado/iniciar).
        """
        try:
            actividad = Actividad.objects.filter(id=actividad_id).first()
            if not actividad:
                return {'ok': False, 'mensaje': 'Actividad no encontrada'}

            resultado = ModeloAhorcado.obtenerPalabraActual(actividad_id)
            if not resultado:
                return {'ok': False, 'mensaje': 'No fue posible cargar las palabras de la actividad'}

            palabra_obj, pistas_db = resultado
            palabra_orig = palabra_obj.palabra.strip().upper()
            palabra_norm = normalizar_palabra(palabra_orig)

            letras_unicas = []
            for ch in palabra_norm:
                if ch.isalpha() and ch not in letras_unicas:
                    letras_unicas.append(ch)

            cant_exponer = min(palabra_obj.letras_expuestas or 1, max(1, len(letras_unicas) - 1))
            letras_expuestas = letras_unicas[:cant_exponer]

            letras_usadas = list(letras_expuestas)
            letras_acertadas = list(letras_expuestas)
            letras_falladas = []

            ahora = timezone.now()
            tablero = self._calcular_estado_tablero(palabra_orig, palabra_norm, letras_acertadas)

            partida = {
                'actividad_id': actividad_id,
                'ahorcado_id': actividad_id,
                'palabra_id': palabra_obj.id,
                'palabra_original': palabra_orig,
                'palabra_normalizada': palabra_norm,
                'pista_inicial': palabra_obj.pista_inicial,
                'pistas_entregadas': [],            # Lista de textos de pistas desbloqueadas
                'indice_pista_mostrada': -1,        # -1 = pista_inicial, 0, 1, 2 para pistas adicionales
                'letras_usadas': letras_usadas,
                'letras_acertadas': letras_acertadas,
                'letras_falladas': letras_falladas,
                'fallos_restantes': 6,
                'pistas_restantes': 3,
                'fecha_inicio': ahora.isoformat(),
                'estado': 'en_progreso',
                'puntos_max': actividad.puntos_max or 100,
                'finalizada': False,
            }
            self._guardar_partida(actividad_id, partida)

            ProgresoActividad.guardarProgresoActividad(
                id_usuario=usuario.id,
                id_actividad=actividad_id,
                resultado={
                    'estado': 'en_progreso',
                    'fecha_inicio': ahora,
                    'sumar_intento': True,
                }
            )

            return {
                'ok': True,
                'actividad_id': actividad_id,
                'estado_tablero': tablero,
                'fallos_restantes': 6,
                'pistas_restantes': 3,
                'pista_label': 'PISTA INICIAL',
                'pista_texto': palabra_obj.pista_inicial,
                'pista_inicial': palabra_obj.pista_inicial,
                'letras_usadas': letras_usadas,
                'letras_falladas': letras_falladas,
                'puntaje': 0,
                'mensaje': 'Partida iniciada con éxito',
            }
        except DatabaseError:
            return {'ok': False, 'mensaje': 'Error de base de datos al iniciar partida'}
        except Exception as e:
            return {'ok': False, 'mensaje': f'Error interno: {str(e)}'}

    def validar_letra(self, usuario, ahorcado_id, letra):
        """
        # Pasos 17 al 25 del diagrama de secuencia (POST /ahorcado/letra).
        """
        partida = self._obtener_partida(ahorcado_id)
        if not partida or partida.get('finalizada'):
            return {'ok': False, 'mensaje': 'No hay una partida activa para esta actividad'}

        letra_norm = normalizar_letra(letra)
        if not letra_norm or not (letra_norm.isalpha() or letra_norm == 'Ñ'):
            return {'ok': False, 'mensaje': 'Por favor ingresa una letra válida'}

        letras_usadas = partida['letras_usadas']
        letras_acertadas = partida['letras_acertadas']
        letras_falladas = partida.get('letras_falladas', [])
        palabra_norm = partida['palabra_normalizada']
        palabra_orig = partida['palabra_original']

        # Letra repetida sin penalizar
        if letra_norm in letras_usadas:
            tablero = self._calcular_estado_tablero(palabra_orig, palabra_norm, letras_acertadas)
            return {
                'ok': True,
                'repetida': True,
                'acierto': letra_norm in letras_acertadas,
                'estado_tablero': tablero,
                'fallos_restantes': partida['fallos_restantes'],
                'pistas_restantes': partida['pistas_restantes'],
                'letras_usadas': letras_usadas,
                'letras_falladas': letras_falladas,
                'mensaje': f'La letra {letra_norm} ya fue elegida anteriormente',
            }

        letras_usadas.append(letra_norm)

        if letra_norm in palabra_norm:
            if letra_norm not in letras_acertadas:
                letras_acertadas.append(letra_norm)

            tablero = self._calcular_estado_tablero(palabra_orig, palabra_norm, letras_acertadas)

            todas_descubiertas = all(
                (ch in letras_acertadas or not ch.isalpha()) for ch in palabra_norm
            )

            if todas_descubiertas:
                resultado_fin = self.finalizar_ahorcado(usuario, ahorcado_id, gano=True)
                return {
                    'ok': True,
                    'acierto': True,
                    'completada': True,
                    'gano': True,
                    'perdio': False,
                    'estado_tablero': tablero,
                    'palabra_revelada': palabra_orig,
                    'fallos_restantes': partida['fallos_restantes'],
                    'pistas_restantes': partida['pistas_restantes'],
                    'letras_usadas': letras_usadas,
                    'letras_falladas': letras_falladas,
                    'puntaje': resultado_fin.get('puntaje', 100),
                    'mensaje': '¡Felicidades! Has descubierto la palabra.',
                }

            self._guardar_partida(ahorcado_id, partida)
            return {
                'ok': True,
                'acierto': True,
                'completada': False,
                'gano': False,
                'perdio': False,
                'estado_tablero': tablero,
                'fallos_restantes': partida['fallos_restantes'],
                'pistas_restantes': partida['pistas_restantes'],
                'letras_usadas': letras_usadas,
                'letras_falladas': letras_falladas,
                'mensaje': f'¡Bien hecho! La letra {letra_norm} es correcta.',
            }

        else:
            partida['fallos_restantes'] -= 1
            if letra_norm not in letras_falladas:
                letras_falladas.append(letra_norm)
            partida['letras_falladas'] = letras_falladas

            tablero = self._calcular_estado_tablero(palabra_orig, palabra_norm, letras_acertadas)

            if partida['fallos_restantes'] <= 0:
                partida['fallos_restantes'] = 0
                resultado_fin = self.finalizar_ahorcado(usuario, ahorcado_id, gano=False)
                tablero_revelado = list(palabra_orig)
                return {
                    'ok': True,
                    'acierto': False,
                    'completada': True,
                    'gano': False,
                    'perdio': True,
                    'estado_tablero': tablero_revelado,
                    'palabra_revelada': palabra_orig,
                    'fallos_restantes': 0,
                    'pistas_restantes': partida['pistas_restantes'],
                    'letras_usadas': letras_usadas,
                    'letras_falladas': letras_falladas,
                    'puntaje': resultado_fin.get('puntaje', 0),
                    'mensaje': f'Partida perdida. La palabra oculta era: {palabra_orig}',
                }

            self._guardar_partida(ahorcado_id, partida)
            return {
                'ok': True,
                'acierto': False,
                'completada': False,
                'gano': False,
                'perdio': False,
                'estado_tablero': tablero,
                'fallos_restantes': partida['fallos_restantes'],
                'pistas_restantes': partida['pistas_restantes'],
                'letras_usadas': letras_usadas,
                'letras_falladas': letras_falladas,
                'mensaje': f'La letra {letra_norm} no se encuentra en la palabra.',
            }

    def solicitar_pista(self, usuario, ahorcado_id):
        """
        # Flujos 1.2 y 1.3:
        Se pueden pedir únicamente 3 pistas (máximo 3 pistas únicas desbloqueables).
        Si ya se desbloquearon las 3 pistas, al volver a solicitar pista vuelve a mostrar
        la primera (Pista 1 -> Pista 2 -> Pista 3 -> Pista 1), ya que solo se ve
        la última pista solicitada en la tarjeta.
        """
        partida = self._obtener_partida(ahorcado_id)
        if not partida or partida.get('finalizada'):
            return {'ok': False, 'mensaje': 'No hay una partida activa'}

        palabra_id = partida['palabra_id']
        pistas_entregadas = partida.get('pistas_entregadas', [])

        try:
            pistas_db = list(
                PistaAhorcado.objects.filter(palabra_id=palabra_id)
                .order_by('orden')[:3]
            )

            # Caso 1: Todavía quedan pistas por desbloquear (máximo 3)
            if len(pistas_entregadas) < len(pistas_db) and len(pistas_entregadas) < 3:
                siguiente_pista = pistas_db[len(pistas_entregadas)]
                pistas_entregadas.append(siguiente_pista.texto)
                partida['pistas_entregadas'] = pistas_entregadas
                partida['pistas_restantes'] = max(0, 3 - len(pistas_entregadas))
                nuevo_indice = len(pistas_entregadas) - 1
                partida['indice_pista_mostrada'] = nuevo_indice
                self._guardar_partida(ahorcado_id, partida)

                pista_num = len(pistas_entregadas)
                return {
                    'ok': True,
                    'pista': siguiente_pista.texto,
                    'pista_label': f'PISTA {pista_num}',
                    'pistas_restantes': partida['pistas_restantes'],
                    'fallos_restantes': partida['fallos_restantes'],
                    'ciclando': False,
                    'mensaje': f'Pista {pista_num} de 3',
                }

            # Caso 2: Ya se entregaron todas las pistas disponibles -> Volver a mostrar la primera y ciclar
            elif len(pistas_entregadas) > 0:
                indice_actual = partida.get('indice_pista_mostrada', 0)
                indice_siguiente = (indice_actual + 1) % len(pistas_entregadas)
                partida['indice_pista_mostrada'] = indice_siguiente
                partida['pistas_restantes'] = 0
                self._guardar_partida(ahorcado_id, partida)

                pista_texto = pistas_entregadas[indice_siguiente]
                pista_num = indice_siguiente + 1
                return {
                    'ok': True,
                    'pista': pista_texto,
                    'pista_label': f'PISTA {pista_num}',
                    'pistas_restantes': 0,
                    'fallos_restantes': partida['fallos_restantes'],
                    'ciclando': True,
                    'mensaje': f'Pista {pista_num} de 3',
                }

            else:
                return {
                    'ok': False,
                    'mensaje': 'Sin pistas disponibles para esta palabra',
                    'pistas_restantes': 0,
                    'fallos_restantes': partida['fallos_restantes'],
                }

        except DatabaseError:
            return {'ok': False, 'mensaje': 'Error de base de datos al solicitar pista'}
        except Exception as e:
            return {'ok': False, 'mensaje': f'Error interno: {str(e)}'}

    def abandonar_actividad(self, usuario, actividad_id):
        """
        # Flujo 1.5 del caso de uso (POST /ahorcado/abandonar).
        """
        partida = self._obtener_partida(actividad_id)
        puntos_max = 100
        fallos = 0
        pistas_usadas = 0

        if partida:
            puntos_max = partida.get('puntos_max', 100)
            fallos = 6 - partida.get('fallos_restantes', 6)
            pistas_usadas = len(partida.get('pistas_entregadas', []))

        puntaje = calcular_puntaje(puntos_max, fallos, pistas_usadas, gano=False)

        ProgresoActividad.guardarProgresoActividad(
            id_usuario=usuario.id,
            id_actividad=actividad_id,
            resultado={
                'estado': 'no_completada',
                'puntaje': puntaje,
                'fecha_completado': timezone.now(),
            }
        )

        self._limpiar_partida(actividad_id)

        redirect_url = '/'
        try:
            act = Actividad.objects.select_related('temario').filter(id=actividad_id).first()
            if act and act.temario and act.temario.mundo_id:
                redirect_url = reverse('temario_mundo', args=[act.temario.mundo_id])
            else:
                redirect_url = reverse('mapa_mundos')
        except Exception:
            redirect_url = '/'

        return {
            'ok': True,
            'redirect_url': redirect_url,
            'mensaje': 'Partida abandonada correctamente',
        }

    def finalizar_ahorcado(self, usuario, actividad_id, gano=True):
        """
        # Pasos 22 al 26 del diagrama de secuencia (POST /ahorcado/finalizar).
        """
        partida = self._obtener_partida(actividad_id)
        if not partida:
            return {'ok': False, 'mensaje': 'No hay partida en curso'}

        fallos_cometidos = 6 - partida.get('fallos_restantes', 6)
        pistas_usadas = len(partida.get('pistas_entregadas', []))
        puntos_max = partida.get('puntos_max', 100)

        puntaje = calcular_puntaje(puntos_max, fallos_cometidos, pistas_usadas, gano=gano)
        estado_final = 'completada' if gano else 'no_completada'
        ahora = timezone.now()

        ProgresoActividad.guardarProgresoActividad(
            id_usuario=usuario.id,
            id_actividad=actividad_id,
            resultado={
                'estado': estado_final,
                'puntaje': puntaje,
                'fecha_completado': ahora,
            }
        )

        partida['finalizada'] = True
        partida['estado'] = estado_final
        partida['puntaje'] = puntaje
        self._guardar_partida(actividad_id, partida)

        siguiente_url = None
        try:
            actividad_actual = Actividad.objects.filter(id=actividad_id).first()
            if actividad_actual:
                sig_act = Actividad.objects.filter(
                    temario_id=actividad_actual.temario_id,
                    orden__gt=actividad_actual.orden
                ).order_by('orden').first()
                if sig_act:
                    siguiente_url = f"/ahorcado/{sig_act.id}/"
        except Exception:
            siguiente_url = None

        return {
            'ok': True,
            'estado': estado_final,
            'puntaje': puntaje,
            'gano': gano,
            'palabra': partida['palabra_original'],
            'siguiente_url': siguiente_url,
            'mensaje': 'Partida finalizada con éxito',
        }
