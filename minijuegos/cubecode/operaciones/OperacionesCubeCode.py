import random


class OperacionesCubeCode:
    PUNTAJE_MAXIMO = 100

    def revolver_bloques(self, bloques):
        revueltos = list(bloques)
        random.shuffle(revueltos)
        return revueltos

    def bloques_correctos(self, ejercicio):
        return list(
            ejercicio.bloques.exclude(orden_solucion__isnull=True).order_by('orden_solucion', 'id')
        )

    def pistas(self, ejercicio):
        return [bloque.pista for bloque in self.bloques_correctos(ejercicio)]

    def validar_solucion(self, ejercicio, ids_enviados):
        try:
            enviados = [int(identificador) for identificador in ids_enviados]
        except (TypeError, ValueError):
            return False
        correctos = [bloque.id for bloque in self.bloques_correctos(ejercicio)]
        return bool(correctos) and enviados == correctos

    def calcular_puntaje(self, hechos, total):
        if not isinstance(hechos, int) or not isinstance(total, int):
            return 0
        if hechos <= 0 or total <= 0:
            return 0
        if hechos >= total:
            return self.PUNTAJE_MAXIMO
        return (hechos * self.PUNTAJE_MAXIMO) // total

    def ejercicio_actual(self, cubecode, hechos_ids):
        hechos = set(hechos_ids or [])
        niveles = sorted(cubecode.niveles.all(), key=lambda nivel: nivel.numero)
        for nivel in niveles:
            ejercicios = sorted(nivel.ejercicios.all(), key=lambda ejercicio: ejercicio.numero)
            for ejercicio in ejercicios:
                if ejercicio.id not in hechos:
                    return ejercicio
        return None

    def serializar_ejercicio(self, ejercicio, hechos_ids, puntaje):
        hechos = set(hechos_ids or [])
        bloques = self.revolver_bloques(ejercicio.bloques.all())
        completados_nivel = sum(1 for item in ejercicio.nivel.ejercicios.all() if item.id in hechos)
        return {
            'id': ejercicio.id,
            'titulo': ejercicio.titulo,
            'objetivo': ejercicio.objetivo,
            'nivel_numero': ejercicio.nivel.numero,
            'nivel_nombre': ejercicio.nivel.nombre,
            'ejercicio_numero': ejercicio.numero,
            'total_nivel': ejercicio.nivel.ejercicios.count(),
            'completados_nivel': completados_nivel,
            'score': puntaje,
            'bloques': [{'id': bloque.id, 'texto': bloque.texto} for bloque in bloques],
        }

    def puntaje_del_nivel(self, cubecode, nivel, total):
        anteriores = 0
        for item in cubecode.niveles.all():
            if item.numero < nivel.numero:
                anteriores += item.ejercicios.count()
        cierre = anteriores + nivel.ejercicios.count()
        return self.calcular_puntaje(cierre, total) - self.calcular_puntaje(anteriores, total)
