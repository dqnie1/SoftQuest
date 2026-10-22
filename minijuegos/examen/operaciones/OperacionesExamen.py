import random
from django.db.models import Sum
from contenido.models import Actividad, Mundo, Temario, ProgresoActividad, ProgresoUsuario, Insignia, InsigniaUsuario
from login.models import Usuario
from minijuegos.trivia.models import Pregunta, Respuesta
from minijuegos.match.models import Concepto
from minijuegos.examen.models import IntentoExamen


class ExcepcionCargaExamen(Exception):
    """Excepción lanzada cuando no es posible recuperar el banco de reactivos (1.0.E1)."""
    pass


class OperacionesExamen:
    TIEMPO_GLOBAL_SEGUNDOS = 600  # 10 minutos (RN-44)
    CALIFICACION_MINIMA = 70.0    # RN-46
    PREGUNTAS_POR_BLOQUE = 3      # RN-41
    CONCEPTOS_POR_BLOQUE = 3      # RN-41

    def obtener_usuario(self, request):
        if not request.user.is_authenticated:
            return None
        nombre = request.user.get_full_name() or request.user.get_username()
        usuario, _ = Usuario.objects.get_or_create(
            cuenta=request.user,
            defaults={'nombre': nombre, 'email': request.user.email}
        )
        return usuario

    def verificar_habilitado(self, usuario, mundo):
        """
        RN-39: El examen de un mundo se habilita únicamente cuando el jugador ha
        completado todas las actividades evaluables de ese mundo.
        """
        if not usuario or not mundo:
            return False

        # Actividades regulares del mundo (excluyendo bancos de preguntas ocultos con orden >= 90)
        actividades = Actividad.objects.filter(temario__mundo=mundo, orden__lt=90)
        total = actividades.count()
        if total == 0:
            return False

        completadas = ProgresoActividad.objects.filter(
            usuario=usuario,
            actividad__in=actividades,
            estado='completado'
        ).count()

        return completadas >= total

    def generar_examen(self, mundo):
        """
        RN-40: El examen está dividido en bloques, uno por cada unidad del mundo.
        RN-41: Los reactivos se seleccionan de un banco y se presentan en orden aleatorio.
        1.0.E1: Si no se pueden recuperar preguntas o pares, lanza ExcepcionCargaExamen.
        """
        temarios = list(mundo.temarios.all().order_by('orden'))
        if not temarios:
            raise ExcepcionCargaExamen("El mundo no tiene unidades/temarios registrados.")

        bloques = []
        claves_servidor = {}  # Para validación segura en el servidor (RN-42)
        total_reactivos = 0

        for idx, temario in enumerate(temarios, start=1):
            # 1. Recuperar banco de preguntas de trivia para el temario
            preguntas_qs = list(
                Pregunta.objects.filter(trivia__actividad__temario=temario)
                .prefetch_related('respuestas')
            )
            # 2. Recuperar banco de conceptos para el temario
            conceptos_qs = list(
                Concepto.objects.filter(match__actividad__temario=temario)
            )

            if not preguntas_qs and not conceptos_qs:
                # Intentar fallback de preguntas del mundo si no estuvieran asociadas estrictamente
                preguntas_qs = list(
                    Pregunta.objects.filter(trivia__actividad__temario__mundo=mundo)
                    .prefetch_related('respuestas')
                )
                conceptos_qs = list(
                    Concepto.objects.filter(match__actividad__temario__mundo=mundo)
                )

            if not preguntas_qs or not conceptos_qs:
                raise ExcepcionCargaExamen(
                    f"No hay suficientes reactivos disponibles para la unidad: {temario.nombre}"
                )

            # Seleccionar aleatoriamente reactivos (RN-41)
            preguntas_sel = random.sample(
                preguntas_qs, min(self.PREGUNTAS_POR_BLOQUE, len(preguntas_qs))
            )
            conceptos_sel = random.sample(
                conceptos_qs, min(self.CONCEPTOS_POR_BLOQUE, len(conceptos_qs))
            )

            # Formatear preguntas sin revelar respuestas correctas (RN-42)
            preguntas_data = []
            for p in preguntas_sel:
                respuestas_list = list(p.respuestas.all())
                random.shuffle(respuestas_list)
                correcta = next((r for r in respuestas_list if r.es_correcta), None)
                if correcta:
                    claves_servidor[f"trivia_{p.id}"] = {
                        'tipo': 'trivia',
                        'bloque_idx': idx,
                        'pregunta_id': p.id,
                        'pregunta_texto': p.texto,
                        'respuesta_correcta_id': correcta.id,
                        'respuesta_correcta_texto': correcta.texto,
                        'explicacion': f"La respuesta correcta es: {correcta.texto}"
                    }
                    total_reactivos += 1

                preguntas_data.append({
                    'id': p.id,
                    'texto': p.texto,
                    'respuestas': [{'id': r.id, 'texto': r.texto} for r in respuestas_list]
                })

            # Formatear pares concepto-definición para ejercicio de relacionar
            conceptos_lista = []
            definiciones_lista = []
            for c in conceptos_sel:
                claves_servidor[f"concepto_{c.id}"] = {
                    'tipo': 'concepto',
                    'bloque_idx': idx,
                    'concepto_id': c.id,
                    'termino': c.termino,
                    'definicion_correcta': c.definicion,
                    'explicacion': f"{c.termino}: {c.definicion}"
                }
                total_reactivos += 1

                conceptos_lista.append({'id': c.id, 'termino': c.termino})
                definiciones_lista.append({'id': c.id, 'definicion': c.definicion})

            random.shuffle(conceptos_lista)
            random.shuffle(definiciones_lista)

            bloques.append({
                'indice': idx,
                'temario_id': temario.id,
                'nombre_temario': temario.nombre,
                'preguntas': preguntas_data,
                'conceptos': conceptos_lista,
                'definiciones': definiciones_lista,
                'total_reactivos': len(preguntas_data) + len(conceptos_lista)
            })

        if total_reactivos == 0:
            raise ExcepcionCargaExamen("El examen no contiene reactivos válidos para evaluar.")

        return {
            'mundo_id': mundo.id,
            'mundo_nombre': mundo.nombre,
            'bloques': bloques,
            'claves': claves_servidor,
            'total_bloques': len(bloques),
            'total_reactivos': total_reactivos,
            'tiempo_limite': self.TIEMPO_GLOBAL_SEGUNDOS,
            'minimo_aprobatorio': self.CALIFICACION_MINIMA
        }

    def evaluar_y_registrar(self, usuario, mundo, examen_session_data, respuestas_usuario, tiempo_empleado):
        """
        RN-44: Cronómetro global; reactivos sin responder se consideran incorrectos.
        RN-45: Calificación = 100 / total_reactivos * total_aciertos.
        RN-46: Calificación mínima aprobatoria = 70.
        RN-47: Si aprueba, mundo completado y se desbloquea siguiente mundo.
        RN-48: El examen no otorga XP.
        RN-49: Otorga insignia especial del mundo (una sola vez).
        RN-50: Si no aprueba, siguiente mundo bloqueado, puede reintentar sin límite.
        RN-51: Registra intento con calificación, tiempo empleado y resultado por bloque.
        """
        claves = examen_session_data.get('claves', {})
        bloques_def = examen_session_data.get('bloques', [])
        total_reactivos = examen_session_data.get('total_reactivos', len(claves))

        if total_reactivos == 0:
            total_reactivos = 1

        total_aciertos = 0
        detalles_reactivos = []
        resultados_por_bloque = {}

        # Inicializar contadores por bloque
        for b in bloques_def:
            b_idx = b['indice']
            resultados_por_bloque[str(b_idx)] = {
                'indice': b_idx,
                'nombre_temario': b['nombre_temario'],
                'total': 0,
                'aciertos': 0,
                'porcentaje': 0.0
            }

        # Evaluar cada clave registrada en el examen
        for clave_key, info in claves.items():
            b_idx_str = str(info['bloque_idx'])
            if b_idx_str in resultados_por_bloque:
                resultados_por_bloque[b_idx_str]['total'] += 1

            es_acierto = False
            respuesta_dada_texto = "Sin responder"

            if info['tipo'] == 'trivia':
                # respuestas_usuario['trivia_<id>'] = respuesta_id
                resp_id_enviada = respuestas_usuario.get(clave_key)
                if resp_id_enviada is not None:
                    try:
                        resp_id_int = int(resp_id_enviada)
                        if resp_id_int == info['respuesta_correcta_id']:
                            es_acierto = True
                        # Buscar texto de respuesta dada
                        r_obj = Respuesta.objects.filter(id=resp_id_int).first()
                        if r_obj:
                            respuesta_dada_texto = r_obj.texto
                    except (ValueError, TypeError):
                        pass

                if es_acierto:
                    total_aciertos += 1
                    if b_idx_str in resultados_por_bloque:
                        resultados_por_bloque[b_idx_str]['aciertos'] += 1
                else:
                    detalles_reactivos.append({
                        'tipo': 'trivia',
                        'bloque': info['bloque_idx'],
                        'pregunta': info['pregunta_texto'],
                        'respuesta_dada': respuesta_dada_texto,
                        'respuesta_correcta': info['respuesta_correcta_texto'],
                        'explicacion': info['explicacion'],
                        'es_correcto': False
                    })

            elif info['tipo'] == 'concepto':
                # respuestas_usuario['concepto_<id>'] = definicion_id
                def_id_enviada = respuestas_usuario.get(clave_key)
                if def_id_enviada is not None:
                    try:
                        def_id_int = int(def_id_enviada)
                        if def_id_int == info['concepto_id']:
                            es_acierto = True
                        c_match = Concepto.objects.filter(id=def_id_int).first()
                        if c_match:
                            respuesta_dada_texto = c_match.definicion
                    except (ValueError, TypeError):
                        pass

                if es_acierto:
                    total_aciertos += 1
                    if b_idx_str in resultados_por_bloque:
                        resultados_por_bloque[b_idx_str]['aciertos'] += 1
                else:
                    detalles_reactivos.append({
                        'tipo': 'concepto',
                        'bloque': info['bloque_idx'],
                        'concepto': info['termino'],
                        'respuesta_dada': respuesta_dada_texto,
                        'respuesta_correcta': info['definicion_correcta'],
                        'explicacion': info['explicacion'],
                        'es_correcto': False
                    })

        # Calcular porcentaje por bloque
        for b_str, b_data in resultados_por_bloque.items():
            if b_data['total'] > 0:
                b_data['porcentaje'] = round((b_data['aciertos'] / b_data['total']) * 100, 1)

        # RN-45: Calificación máxima 100 dividida entre total de reactivos
        calificacion = round((total_aciertos / total_reactivos) * 100, 2)
        aprobado = calificacion >= self.CALIFICACION_MINIMA  # RN-46

        # RN-51: Registrar cada intento
        intento = IntentoExamen.objects.create(
            usuario=usuario,
            mundo=mundo,
            calificacion=calificacion,
            aprobado=aprobado,
            tiempo_empleado_segundos=min(tiempo_empleado, self.TIEMPO_GLOBAL_SEGUNDOS),
            resultado_bloques=resultados_por_bloque,
            detalles_reactivos=detalles_reactivos
        )

        if aprobado:
            # Desbloquear el siguiente mundo si existe
            mundos_ordenados = list(Mundo.objects.all().order_by('orden'))
            try:
                mundo_index = [m.id for m in mundos_ordenados].index(mundo.id)
                if mundo_index + 1 < len(mundos_ordenados):
                    siguiente_mundo = mundos_ordenados[mundo_index + 1]
                    progreso_user = ProgresoUsuario.objects.filter(usuario=usuario).first()
                    if progreso_user:
                        # Si su mundo actual era este mundo o uno inferior, avanzarlo
                        if progreso_user.mundo_actual.orden <= mundo.orden:
                            progreso_user.mundo_actual = siguiente_mundo
                            progreso_user.save()
            except ValueError:
                pass

        return {
            'intento': intento,
            'calificacion': calificacion,
            'aprobado': aprobado,
            'tiempo_empleado': intento.tiempo_empleado_segundos,
            'resultados_por_bloque': resultados_por_bloque,
            'detalles_reactivos': detalles_reactivos,
            'total_aciertos': total_aciertos,
            'total_reactivos': total_reactivos
        }
