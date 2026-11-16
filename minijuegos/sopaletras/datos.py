"""
Definición de palabras y conceptos pedagógicos para CU-12 Resolver sopa de letras.
Reglas de negocio asociadas: RN-81, RN-82, RN-83, RN-90, RN-91.
"""

PALABRAS_SOPALETRAS = [
    {
        "palabra": "REQUISITO",
        "nombre": "Requisito",
        "definicion": "Condición o capacidad que debe cumplir el sistema para satisfacer una necesidad del usuario.",
        "explicacion": "Describe qué debe hacer o cómo debe comportarse el software, no cómo se programa.",
        "tipo_ejemplo": "Ejemplo",
        "ejemplo": "“El jugador debe poder reiniciar un nivel” es un requisito funcional.",
        "color": "#818cf8",
    },
    {
        "palabra": "ACTOR",
        "nombre": "Actor",
        "definicion": "Rol externo que interactúa con el sistema dentro de un caso de uso.",
        "explicacion": "Puede ser una persona u otro sistema; representa un papel, no a un individuo concreto.",
        "tipo_ejemplo": "Ejemplo",
        "ejemplo": "En SoftQuest, el Jugador es el actor que inicia el caso de uso Jugar sopa de letras.",
        "color": "#34d399",
    },
    {
        "palabra": "SPRINT",
        "nombre": "Sprint",
        "definicion": "Iteración corta de tiempo fijo en la que un equipo Scrum entrega un incremento del producto.",
        "explicacion": "Suele durar de una a cuatro semanas y termina con una revisión del trabajo hecho.",
        "tipo_ejemplo": "Cómo se aplica",
        "ejemplo": "Un equipo planea un sprint de dos semanas para entregar el módulo de inicio de sesión.",
        "color": "#fbbf24",
    },
    {
        "palabra": "BACKLOG",
        "nombre": "Backlog",
        "definicion": "Lista priorizada de todo el trabajo pendiente de un producto.",
        "explicacion": "El dueño del producto la ordena según el valor y cambia conforme se aprende del proyecto.",
        "tipo_ejemplo": "Cómo se aplica",
        "ejemplo": "Antes de cada sprint, el equipo toma del backlog las historias de mayor prioridad.",
        "color": "#a78bfa",
    },
    {
        "palabra": "PRUEBA",
        "nombre": "Prueba",
        "definicion": "Actividad que ejecuta el software con casos definidos para verificar que se comporta como se espera.",
        "explicacion": "Ayuda a detectar defectos antes de que lleguen al usuario.",
        "tipo_ejemplo": "Ejemplo",
        "ejemplo": "Una prueba comprueba que, al encontrar las 8 palabras, el sistema marque la actividad como completada.",
        "color": "#fb923c",
    },
    {
        "palabra": "DEFECTO",
        "nombre": "Defecto",
        "definicion": "Falla en el código o en un documento que puede provocar un comportamiento incorrecto.",
        "explicacion": "Se registra, se prioriza y se corrige; entre más temprano se detecta, menos cuesta arreglarlo.",
        "tipo_ejemplo": "Cómo se aplica",
        "ejemplo": "Una revisión en pares encuentra un defecto en un caso de uso y lo anota en la bitácora.",
        "color": "#f472b6",
    },
    {
        "palabra": "VERSION",
        "nombre": "Versión",
        "definicion": "Estado identificable de un producto o documento en un momento determinado.",
        "explicacion": "Permite saber qué cambió, volver a un estado anterior y trabajar en equipo sin perder trabajo.",
        "tipo_ejemplo": "Cómo se aplica",
        "ejemplo": "Un equipo usa Git para guardar cada versión del SRS: V1, V2 y V3.",
        "color": "#38bdf8",
    },
    {
        "palabra": "REFACTOR",
        "nombre": "Refactorización",
        "definicion": "Mejorar la estructura interna del código sin cambiar su comportamiento visible.",
        "explicacion": "Hace el código más claro y fácil de mantener; se apoya en pruebas para no romper nada.",
        "tipo_ejemplo": "Cómo se aplica",
        "ejemplo": "Dividir una función de 200 líneas en funciones pequeñas con nombres claros.",
        "color": "#a3e635",
    },
]
