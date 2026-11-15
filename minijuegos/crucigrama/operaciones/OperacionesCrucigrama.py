import unicodedata


class OperacionesCrucigrama:
    """
    Lógica de negocio del CU-09: Resolver Crucigrama.
    Implementa las reglas RN-52 a RN-66.
    """

    # Configuración por defecto
    VIDAS_INICIALES = 3          # RN-58
    TIEMPO_LIMITE_SEG = 180      # RN-60
    XP_MAXIMO = 100              # RN-G01, RN-64

    @classmethod
    def preparar_crucigrama(cls, crucigrama):
        """
        Prepara la estructura completa del crucigrama para enviar al frontend.
        Retorna un dict con la cuadrícula y las palabras.
        """
        palabras_bd = list(crucigrama.palabras.all())
        total = len(palabras_bd)

        palabras = []
        for p in palabras_bd:
            palabras.append({
                "id": p.id,
                "numero": p.numero,
                "direccion": p.direccion,
                "fila_inicio": p.fila_inicio,
                "columna_inicio": p.columna_inicio,
                "respuesta": cls.normalizar(p.respuesta),
                "longitud": len(p.respuesta),
                "enunciado": p.enunciado,
                "explicacion": p.explicacion,
            })

        return {
            "actividad_id": crucigrama.actividad_id,
            "filas": crucigrama.filas,
            "columnas": crucigrama.columnas,
            "tiempo_limite_seg": crucigrama.tiempo_limite_seg,
            "total_palabras": total,
            "palabras": palabras,
        }

    @staticmethod
    def normalizar(texto):
        """
        RN-53: No distingue mayúsculas/minúsculas ni acentos.
        Convierte a mayúsculas y elimina diacríticos.
        """
        texto = texto.upper().strip()
        # Descomponer Unicode, eliminar marcas de combinación (acentos)
        nfkd = unicodedata.normalize('NFD', texto)
        return ''.join(c for c in nfkd if not unicodedata.combining(c))

    @classmethod
    def validar_palabra(cls, palabra_enviada, respuesta_correcta):
        """
        RN-53, RN-54: Valida si la palabra enviada coincide con la respuesta.
        Normaliza ambos lados antes de comparar.
        """
        return cls.normalizar(palabra_enviada) == cls.normalizar(respuesta_correcta)

    @staticmethod
    def calcular_xp(palabras_primer_intento, total_palabras):
        """
        RN-64, RN-65: El XP se obtiene dividiendo 100 entre el total de palabras;
        solo suman las palabras resueltas al primer intento.
        RN-G01: Máximo 100 XP.
        """
        try:
            primer = int(palabras_primer_intento)
            total = int(total_palabras)
        except (TypeError, ValueError):
            return 0

        if total <= 0:
            return 0

        primer = max(0, min(primer, total))
        xp = round((primer / total) * 100)
        return max(0, min(100, xp))

    @staticmethod
    def es_intento_repetido(intentos_previos, palabra_actual):
        """
        RN-57: Si la palabra incorrecta es idéntica a un intento incorrecto
        anterior de esa misma palabra, no pierde una vida.
        """
        normalizada = OperacionesCrucigrama.normalizar(palabra_actual)
        return normalizada in [
            OperacionesCrucigrama.normalizar(i) for i in intentos_previos
        ]

    @staticmethod
    def validar_resultado(palabras_resueltas, total_palabras, vidas_restantes):
        """
        Verifica que los datos enviados desde el cliente sean consistentes.
        """
        try:
            resueltas = int(palabras_resueltas)
            total = int(total_palabras)
            vidas = int(vidas_restantes)
        except (TypeError, ValueError):
            return False

        return 0 <= resueltas <= total and 0 <= vidas <= 3
