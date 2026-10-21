import random


class OperacionesPacman:
    VIDAS = 3
    PUNTOS_LINEA_DEFECTO = 100

    # Leyenda: # pared  . camino  P inicio jugador  D debugger (spawn enemigos)
    # Todos los mapas deben tener exactamente una 'P' y al menos una 'D'.
    # Deben ser rectangulares (todas las filas del mismo largo).
    MAPAS = [
        # --- Mapa 0: Laberinto clasico ---
        [
            "###################",
            "#P.....#..........#",
            "#.###..#.########.#",
            "#...#..#..........#",
            "###.#..######.###.#",
            "#...#.............#",
            "#.######.########.#",
            "#......#..........#",
            "#.####.#.######.#.#",
            "#...............#.#",
            "#####.#####.#####.#",
            "#.....#...#.......#",
            "#.#####...#####.#.#",
            "#.......#.......#.#",
            "#.#####.#.#####.#.#",
            "#...D...#.......#.#",
            "#.#######.#####.#.#",
            "#.................#",
            "###################",
        ],
        # --- Mapa 1: Cruz central ---
        [
            "###################",
            "#.................#",
            "#.###.#####.###.#.#",
            "#.#.............#.#",
            "#.#.###.###.###.#.#",
            "#.#.#.........#.#.#",
            "#...#.#######.#...#",
            "#P..#....D....#...#",
            "#...#.#######.#...#",
            "#.#.#.........#.#.#",
            "#.#.###.###.###.#.#",
            "#.#.............#.#",
            "#.###.#####.###.#.#",
            "#.................#",
            "###.###########.###",
            "#.................#",
            "#.###.#########.#.#",
            "#.................#",
            "###################",
        ],
        # --- Mapa 3: Cuadricula abierta ---
        [
            "###################",
            "#P..#.....#.....#.#",
            "#.#.#.###.#.###.#.#",
            "#.#...#.....#...#.#",
            "#.#####.###.##,##.#",
            "#.......#.#.......#",
            "#.#.###.#.#.#####.#",
            "#.#...#.#.#.#...#.#",
            "#.#.#.#.#.#.#.#.#.#",
            "#...#.....D...#...#",
            "#.#.####.####.#.#.#",
            "#.#.#.........#.#.#",
            "#.#.#.#######.#.#.#",
            "#.#...#.....#...#.#",
            "#.#.###.###.#####.#",
            "#.......#.#.......#",
            "#.#.###.#.#.#####.#",
            "#.................#",
            "###################",
        ],
    ]

    # Spawns por defecto; se calculan dinamicamente en preparar_nivel
    ESPERA_INICIAL_MS = 2000
    ESPERA_ENTRE_ENEMIGOS_MS = 1500

    # ------------------------------------------------------------------
    # Seleccion de mapa
    # ------------------------------------------------------------------
    @classmethod
    def mapa_aleatorio(cls):
        """Devuelve una copia de un mapa escogido al azar entre los disponibles."""
        return list(random.choice(cls.MAPAS))

    @classmethod
    def _spawns_enemigos(cls, mapa):
        """Encuentra todas las posiciones 'D' en el mapa como lista de (x, y)."""
        spawns = []
        for y, fila in enumerate(mapa):
            for x, celda in enumerate(fila):
                if celda == "D":
                    spawns.append((x, y))
        return spawns

    @classmethod
    def _posicion_jugador(cls, mapa):
        """Devuelve (x, y) de la 'P' en el mapa."""
        for y, fila in enumerate(mapa):
            for x, celda in enumerate(fila):
                if celda == "P":
                    return x, y
        return 1, 1  # fallback

    # ------------------------------------------------------------------
    # Preparacion del tablero
    # ------------------------------------------------------------------
    @classmethod
    def preparar_nivel(cls, nivel, mapa=None):
        """Lista de PacmanLineas REVUELTA + enemigos, lista para mandarse al navegador.
        No incluye orden, pista ni explicacion: esos datos los entrega el servidor poco a poco."""
        lineas = list(nivel.lineas.all())
        random.shuffle(lineas)
        n = max(0, nivel.num_enemigos)

        spawns = cls._spawns_enemigos(mapa) if mapa else []
        enemigos = []
        for i in range(n):
            if spawns:
                sx, sy = spawns[i % len(spawns)]
            else:
                sx, sy = 9, 9  # fallback
            enemigos.append({
                "x": sx,
                "y": sy,
                "intervalo_ms": nivel.velocidad_ms or 560,
                "espera_ms": cls.ESPERA_INICIAL_MS + i * cls.ESPERA_ENTRE_ENEMIGOS_MS,
            })

        return {
            "id": nivel.id,
            "titulo": nivel.titulo,
            "total_lineas": len(lineas),
            "lineas": [{"id": l.id, "codigo": l.codigo} for l in lineas],
            "num_enemigos": n,
            "enemigos": enemigos,
            "velocidad_ms": nivel.velocidad_ms,
            "espera_inicial_ms": cls.ESPERA_INICIAL_MS,
            "espera_entre_enemigos_ms": cls.ESPERA_ENTRE_ENEMIGOS_MS,
        }

    @staticmethod
    def nuevo_juego(ids_niveles, mapa):
        """Crea el estado inicial del juego guardando tambien el mapa elegido."""
        return {"total": 0, "bases": {}, "niveles": list(ids_niveles), "nivel": None, "mapa": mapa}

    @classmethod
    def iniciar_nivel(cls, juego, nivel, nuevo_juego=False):
        if nuevo_juego:
            juego["total"] = 0
            juego["bases"] = {}
        base = juego["bases"].setdefault(str(nivel.id), juego["total"])
        lineas = [
            {"id": l.id, "codigo": l.codigo, "pista": l.pista, "explicacion": l.explicacion,
             "puntos": l.puntos or cls.PUNTOS_LINEA_DEFECTO}
            for l in sorted(nivel.lineas.all(), key=lambda l: l.orden)
        ]
        juego["nivel"] = {
            "id": nivel.id, "titulo": nivel.titulo, "salida": nivel.salida, "lineas": lineas,
            "recogidas": [], "vidas": cls.VIDAS, "bugs": 0, "puntaje": base, "base": base,
            "finalizado": False, "final": None,
        }
        return juego["nivel"]

    # ------------------------------------------------------------------
    # Fragmentos (lineas del reto)
    # ------------------------------------------------------------------
    @staticmethod
    def siguiente(estado):
        """Datos de la linea que toca recoger (None si ya estan todas)."""
        i = len(estado["recogidas"])
        if i >= len(estado["lineas"]):
            return None
        l = estado["lineas"][i]
        return {"id": l["id"], "pista": l["pista"]}

    @classmethod
    def validar_orden_fragmento(cls, estado, linea_id):
        sig = cls.siguiente(estado)
        return sig is not None and str(sig["id"]) == str(linea_id)

    @staticmethod
    def registrar_fragmento(estado):
        l = estado["lineas"][len(estado["recogidas"])]
        estado["recogidas"].append(l["id"])
        estado["puntaje"] += l["puntos"]
        return l

    # ------------------------------------------------------------------
    # Vidas
    # ------------------------------------------------------------------
    @staticmethod
    def quitar_vida(estado):
        estado["vidas"] = max(0, estado["vidas"] - 1)
        estado["bugs"] += 1
        return estado["vidas"]

    @classmethod
    def devolver_fragmento_al_tablero(cls, estado):
        """Quita la ultima linea recogida (el cliente la coloca en otra casilla). Devuelve su id."""
        if not estado["recogidas"]:
            return None
        linea_id = estado["recogidas"].pop()
        linea = next(l for l in estado["lineas"] if l["id"] == linea_id)
        estado["puntaje"] -= linea["puntos"]
        return linea_id

    # ------------------------------------------------------------------
    # Fin de nivel
    # ------------------------------------------------------------------
    @classmethod
    def calcular_resumen_nivel(cls, estado):
        """Funcion pura: no modifica el estado, la vista lo confirma despues de guardar en BD."""
        return {
            "titulo": estado["titulo"],
            "n": len(estado["lineas"]),
            "vidas": estado["vidas"],
            "bugs": estado["bugs"],
            "puntos_nivel": estado["puntaje"] - estado["base"],
            "puntaje_total": estado["puntaje"],
            "salida": estado["salida"],
            "codigo": [l["codigo"] for l in estado["lineas"]],
        }
