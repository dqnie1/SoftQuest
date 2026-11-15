import random

from minijuegos.ninjacode.models import TipoRequisitoNinja


class OperacionesNinjaCode:
    PUNTOS_ACIERTO = 25
    VIDAS = 3
    FRUTAS_POR_NIVEL = 16
    ACIERTOS_EN_MAZO = 10

    def cargar_requisitos(self, ninjacode):
        if ninjacode is None:
            return []
        return list(ninjacode.requisitos.all().order_by('id'))

    def serializar_requisitos(self, requisitos):
        return [
            {'id': item.id, 'texto': item.texto, 'tipo': item.tipo}
            for item in requisitos
        ]

    def tiene_contenido(self, requisitos):
        tipos = {item.tipo for item in requisitos}
        return (
            TipoRequisitoNinja.FUNCIONAL in tipos
            and TipoRequisitoNinja.NO_FUNCIONAL in tipos
        )

    def revolver(self, items):
        revueltos = list(items)
        random.shuffle(revueltos)
        return revueltos

    def es_corte_correcto(self, tipo, nivel):
        if nivel == 1:
            return tipo == TipoRequisitoNinja.FUNCIONAL
        if nivel == 2:
            return tipo == TipoRequisitoNinja.NO_FUNCIONAL
        return False

    def calcular_puntaje(self, aciertos, puntos_max=100):
        if not isinstance(aciertos, int) or aciertos <= 0:
            return 0
        tope = puntos_max if isinstance(puntos_max, int) and puntos_max > 0 else 100
        return min(tope, aciertos * self.PUNTOS_ACIERTO)

    def evaluar_partida(self, requisitos, cortes, niveles_completados, puntos_max=100):
        por_id = {item.id: item for item in requisitos}
        aciertos = 0
        errores = 0
        score1 = 0
        score2 = 0
        detallados = []

        for corte in cortes:
            try:
                requisito_id = int(corte['id'])
                nivel = int(corte['nivel'])
            except (TypeError, ValueError, KeyError):
                return {'ok': False, 'error': 'Corte invalido'}
            if nivel not in (1, 2):
                return {'ok': False, 'error': 'Nivel invalido'}
            requisito = por_id.get(requisito_id)
            if requisito is None:
                return {'ok': False, 'error': 'Requisito no encontrado'}
            correcto = self.es_corte_correcto(requisito.tipo, nivel)
            if correcto:
                aciertos += 1
                if nivel == 1:
                    score1 += self.PUNTOS_ACIERTO
                else:
                    score2 += self.PUNTOS_ACIERTO
            else:
                errores += 1
            detallados.append({
                'id': requisito_id,
                'nivel': nivel,
                'correcto': correcto,
            })

        completado = (
            int(niveles_completados or 0) == 2
            and errores < self.VIDAS
        )
        total = self.calcular_puntaje(aciertos, puntos_max)
        return {
            'ok': True,
            'completado': completado,
            'aciertos': aciertos,
            'errores': errores,
            'score1': min(puntos_max, score1) if completado else score1,
            'score2': min(puntos_max, score2) if completado else score2,
            'puntaje': total if completado else 0,
            'detalles': detallados,
        }
