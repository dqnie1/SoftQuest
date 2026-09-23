from django.db.models import Sum

from contenido.models import Mundo, ProgresoActividad, ProgresoUsuario, Usuario


class OperacionesContenido:
    ESTADO_COMPLETADO = 'completado'

    def obtener_usuario(self, request):
        uid = request.session.get('usuario_id')
        if uid:
            usuario = Usuario.objects.filter(pk=uid).first()
            if usuario:
                return usuario

        usuario = Usuario.objects.order_by('id').first()
        if usuario:
            request.session['usuario_id'] = usuario.id
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
        jugable = tipo in ('trivia', 'memorama')
        completada = self.actividad_completada(actividad, progresos)
        progreso = progresos.get(actividad.id)

        if tipo == 'trivia':
            etiqueta = 'Trivia'
            url_name = 'trivia_detalle'
        elif tipo == 'memorama':
            etiqueta = 'Memorama'
            url_name = 'memorama_detalle'
        elif tipo in ('match_juego', 'match'):
            etiqueta = 'Match'
            url_name = None
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
