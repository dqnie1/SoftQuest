import random


class OperacionesTrivia:
    UMBRAL_APROBATORIO = 70

    def revolver_respuestas(self, respuestas):
        revueltas = list(respuestas)
        random.shuffle(revueltas)
        return revueltas

    def validar_respuesta(self, respuesta):
        return bool(respuesta and respuesta.es_correcta)

    def calcular_calificacion(self, aciertos, total):
        porcentaje = round((aciertos / total) * 100) if total else 0
        return {
            'aciertos': aciertos,
            'total': total,
            'porcentaje': porcentaje,
            'aprobado': porcentaje >= self.UMBRAL_APROBATORIO,
        }
