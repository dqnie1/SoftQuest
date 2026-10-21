import random


class OperacionesSnake:
    # Estados de la partida segun diagrama de secuencia y UML
    ESTADO_ESPERANDO_INICIO = "ESPERANDO_INICIO"
    ESTADO_EN_CURSO = "EN_CURSO"
    ESTADO_MOSTRANDO_INFO = "MOSTRANDO_INFO"
    ESTADO_GANADA = "GANADA"
    ESTADO_PERDIDA = "PERDIDA"

    # Motivos de finalizacion segun diagrama de secuencia
    MOTIVO_TODOS_OBJETIVOS = "RECOLECTO_TODOS_LOS_OBJETIVOS"
    MOTIVO_TOCO_OBSTACULO = "TOCO_OBSTACULO"
    MOTIVO_CHOQUE_MURO = "CHOQUE_MURO"
    MOTIVO_CHOQUE_CUERPO = "CHOQUE_CUERPO"

    # Configuracion de tablero por defecto
    FILAS_DEFECTO = 26
    COLUMNAS_DEFECTO = 26
    VELOCIDAD_MS_DEFECTO = 170

    @classmethod
    def preparar_nivel(cls, nivel):
        """
        Prepara la estructura del nivel con posiciones para cada item en la cuadricula.
        Asegura que no se posicionen sobre la posicion inicial de la serpiente ni se solapen.
        """
        filas = nivel.filas or cls.FILAS_DEFECTO
        columnas = nivel.columnas or cls.COLUMNAS_DEFECTO
        velocidad_ms = nivel.velocidad_ms or cls.VELOCIDAD_MS_DEFECTO

        # Posicion inicial reservada para la serpiente (cabeza y cuerpo inicial centrado)
        centro_x = columnas // 2
        centro_y = filas // 2
        posiciones_ocupadas = {
            (centro_x, centro_y),
            (centro_x - 1, centro_y),
            (centro_x - 2, centro_y),
        }

        # Generar posiciones aleatorias unicas dentro del tablero con margen de 1 casilla del borde
        todas_posiciones = [
            (x, y)
            for x in range(1, columnas - 1)
            for y in range(1, filas - 1)
            if (x, y) not in posiciones_ocupadas
        ]
        random.shuffle(todas_posiciones)

        items_bd = list(nivel.items.all())
        items_preparados = []
        total_objetivos = 0

        for idx, item in enumerate(items_bd):
            if idx < len(todas_posiciones):
                x, y = todas_posiciones[idx]
            else:
                x, y = (idx % (columnas - 2) + 1, idx % (filas - 2) + 1)

            if item.es_objetivo:
                total_objetivos += 1

            items_preparados.append({
                "id": item.id,
                "identificador": item.identificador,
                "categoria": item.categoria,
                "texto": item.texto,
                "es_objetivo": item.es_objetivo,
                "explicacion": item.explicacion,
                "contraste": item.contraste,
                "x": x,
                "y": y,
            })

        return {
            "id": nivel.id,
            "numero": nivel.numero,
            "titulo": nivel.titulo,
            "tema": nivel.tema,
            "instrucciones": nivel.instrucciones,
            "filas": filas,
            "columnas": columnas,
            "velocidad_ms": velocidad_ms,
            "total_objetivos": total_objetivos,
            "items": items_preparados,
        }

    @staticmethod
    def calcular_puntaje(objetivos_recolectados, total_objetivos):
        """
        RN-18: El maximo de score (experiencia) obtenido es de 100 y se obtiene
        dividiendo el 100 entre el numero de requerimientos no funcionales (objetivos) obtenido.
        Tambien aplica cuando el jugador pierde (puntaje parcial).
        """
        try:
            objs = int(objetivos_recolectados)
            total = int(total_objetivos)
        except (TypeError, ValueError):
            return 0

        if total <= 0:
            return 100 if objs > 0 else 0

        objs = max(0, min(objs, total))
        # Puntaje proporcional sobre 100
        puntaje = round((objs / total) * 100)
        return max(0, min(100, puntaje))

    @staticmethod
    def validar_resultado(objetivos_recolectados, total_objetivos):
        """
        Verifica que los datos enviados desde el cliente sean consistentes.
        """
        try:
            objs = int(objetivos_recolectados)
            total = int(total_objetivos)
        except (TypeError, ValueError):
            return False

        return 0 <= objs <= total
