from django.db.models import Sum

from contenido.models import Actividad, Mundo, ProgresoActividad, ProgresoUsuario
from login.models import Usuario


class OperacionesContenido:
    ESTADO_COMPLETADO = 'completado'

    def obtener_usuario(self, request):
        if not request.user.is_authenticated:
            return None

        nombre = request.user.get_full_name() or request.user.get_username()
        usuario, _ = Usuario.objects.get_or_create(
            cuenta=request.user,
            defaults={
                'nombre': nombre,
                'email': request.user.email,
            },
        )
        return usuario

    def progresos_por_actividad(self, usuario):
        if not usuario:
            return {}
        return {
            progreso.actividad_id: progreso
            for progreso in ProgresoActividad.objects.filter(usuario=usuario)
        }

    def actividad_completada(self, actividad, progresos):
        progreso = progresos.get(actividad.id)
        return bool(
            progreso and (progreso.estado or '').lower() == self.ESTADO_COMPLETADO
        )

    def temario_completado(self, temario, progresos):
        actividades = list(temario.actividades.all())
        if not actividades:
            return False
        return all(self.actividad_completada(act, progresos) for act in actividades)

    def mundo_completado(self, mundo, progresos):
        temarios = list(mundo.temarios.all())
        if not temarios:
            return False
        return all(self.temario_completado(temario, progresos) for temario in temarios)

    def xp_usuario(self, usuario):
        if not usuario:
            return 0
        total = ProgresoActividad.objects.filter(usuario=usuario).aggregate(
            total=Sum('puntaje')
        )['total']
        return int(total or 0)

    def construir_mapa(self, mundos, progresos):
        items = []
        anterior_completado = True
        actual_asignado = False

        for mundo in mundos:
            completado = self.mundo_completado(mundo, progresos)
            desbloqueado = anterior_completado
            es_actual = desbloqueado and not completado and not actual_asignado
            if es_actual:
                actual_asignado = True

            if desbloqueado:
                estado = 'completado' if completado else ('actual' if es_actual else 'disponible')
            else:
                estado = 'bloqueado'

            items.append({
                'mundo': mundo,
                'estado': estado,
                'desbloqueado': desbloqueado,
                'completado': completado,
            })
            anterior_completado = completado

        if not actual_asignado:
            for item in reversed(items):
                if item['desbloqueado']:
                    if item['estado'] == 'disponible':
                        item['estado'] = 'actual'
                    break

        return items

    def construir_temarios(self, mundo, progresos):
        items = []
        anterior_completado = True
        actual_asignado = False

        for temario in mundo.temarios.all():
            completado = self.temario_completado(temario, progresos)
            desbloqueado = anterior_completado
            es_actual = desbloqueado and not completado and not actual_asignado
            if es_actual:
                actual_asignado = True

            if desbloqueado:
                estado = 'completado' if completado else ('actual' if es_actual else 'disponible')
            else:
                estado = 'bloqueado'

            actividades = list(temario.actividades.all())
            xp_ganado = 0
            xp_max = 0
            for actividad in actividades:
                xp_max += actividad.puntos_max or 0
                progreso = progresos.get(actividad.id)
                if progreso:
                    xp_ganado += progreso.puntaje or 0

            items.append({
                'temario': temario,
                'estado': estado,
                'desbloqueado': desbloqueado,
                'completado': completado,
                'xp_ganado': xp_ganado,
                'xp_max': xp_max,
                'actividades': [
                    self._serializar_actividad(actividad, progresos)
                    for actividad in actividades
                ],
            })
            anterior_completado = completado

        if not actual_asignado:
            for item in reversed(items):
                if item['desbloqueado']:
                    if item['estado'] == 'disponible':
                        item['estado'] = 'actual'
                    break

        return items

    def _serializar_actividad(self, actividad, progresos):
        tipo = (actividad.tipo or '').strip().lower()
        jugable = tipo in ('trivia', 'memorama', 'match_juego', 'match', 'pacman')
        completada = self.actividad_completada(actividad, progresos)
        progreso = progresos.get(actividad.id)

        if tipo == 'trivia':
            etiqueta = 'Trivia'
            url_name = 'trivia:trivia_detalle'
        elif tipo == 'memorama':
            etiqueta = 'Memorama'
            url_name = 'memorama_detalle'
        elif tipo in ('match_juego', 'match'):
            etiqueta = 'Match'
            url_name = 'match:match_detalle'
        elif tipo == 'pacman':
            etiqueta = 'Pacman'
            url_name = 'pacman:jugar'
        else:
            etiqueta = actividad.tipo or 'Actividad'
            url_name = None

        return {
            'actividad': actividad,
            'tipo': tipo,
            'etiqueta': etiqueta,
            'url_name': url_name,
            'jugable': jugable,
            'completada': completada,
            'puntaje': progreso.puntaje if progreso else 0,
        }

    def estadisticas(self, usuario, mapa, temarios_globales, progresos):
        total_mundos = len(mapa)
        mundos_completados = sum(1 for item in mapa if item['completado'])
        temarios_completados = sum(
            1 for temario in temarios_globales
            if self.temario_completado(temario, progresos)
        )
        return {
            'xp': self.xp_usuario(usuario),
            'mundos_completados': mundos_completados,
            'total_mundos': total_mundos,
            'temarios_completados': temarios_completados,
        }

    def sincronizar_mundo_actual(self, usuario, mapa):
        if not usuario or not mapa:
            return

        actual = None
        for item in mapa:
            if item['estado'] == 'actual':
                actual = item['mundo']
                break
        if actual is None:
            for item in reversed(mapa):
                if item['desbloqueado']:
                    actual = item['mundo']
                    break
        if actual is None:
            return

        ProgresoUsuario.objects.update_or_create(
            usuario=usuario,
            defaults={'mundo_actual': actual},
        )

    def actualizar_progreso_mundo(self, usuario):
        if not usuario:
            return None

        mundos = list(Mundo.objects.all().order_by('orden'))
        if not mundos:
            return None

        progreso_usuario, _ = ProgresoUsuario.objects.get_or_create(
            usuario=usuario,
            defaults={'mundo_actual': mundos[0]}
        )

        # Determinar el mundo más avanzado al que el usuario tiene acceso.
        # Criterios (en orden de precedencia):
        #   A) Mundo completado si TODAS sus actividades visibles (orden<90) están en estado 'completado'.
        #   B) Mundo desbloqueado si tiene un IntentoExamen aprobado para el mundo anterior.
        # IMPORTANTE: nunca retroceder — si ProgresoUsuario ya apunta a un mundo más avanzado
        # (guardado por el examen), se respeta ese valor y solo se avanza.

        from minijuegos.examen.models import IntentoExamen

        # Determinar el mundo más avanzado desbloqueado via examen aprobado.
        # Si el usuario aprobó el examen del mundo N (orden=X), entonces
        # los mundos 1..N están superados y el mundo N+1 está desbloqueado.
        examenes_aprobados = IntentoExamen.objects.filter(
            usuario=usuario, aprobado=True
        ).select_related('mundo').order_by('-mundo__orden')

        # Orden máximo de mundo cuyo examen fue aprobado (0 si ninguno)
        max_orden_aprobado = 0
        for ie in examenes_aprobados:
            if ie.mundo.orden > max_orden_aprobado:
                max_orden_aprobado = ie.mundo.orden

        mundo_calculado = mundos[0]

        for i, mundo in enumerate(mundos):
            # Criterio A: examen de ESTE mundo fue aprobado → superado
            examen_aprobado = (mundo.orden <= max_orden_aprobado)

            # Criterio B: todas las actividades visibles completadas
            actividades = Actividad.objects.filter(temario__mundo=mundo, orden__lt=90)
            total_act = actividades.count()

            if total_act == 0:
                actividades_completas = True
            else:
                completadas = ProgresoActividad.objects.filter(
                    usuario=usuario,
                    actividad__in=actividades,
                    estado=self.ESTADO_COMPLETADO,
                ).count()
                actividades_completas = (completadas >= total_act)

            mundo_superado = examen_aprobado or actividades_completas

            if mundo_superado:
                if i + 1 < len(mundos):
                    mundo_calculado = mundos[i + 1]
                else:
                    mundo_calculado = mundo
            else:
                mundo_calculado = mundo
                break

        # Nunca retroceder: conservar el mundo más avanzado entre el calculado y el almacenado
        if mundo_calculado.orden >= progreso_usuario.mundo_actual.orden:
            mundo_final = mundo_calculado
        else:
            mundo_final = progreso_usuario.mundo_actual

        if progreso_usuario.mundo_actual_id != mundo_final.id:
            progreso_usuario.mundo_actual = mundo_final
            progreso_usuario.save()

        return progreso_usuario

