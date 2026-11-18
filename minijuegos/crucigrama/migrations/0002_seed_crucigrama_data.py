from django.db import migrations


def crear_datos_iniciales_crucigrama(apps, schema_editor):
    Actividad = apps.get_model('contenido', 'Actividad')
    Temario = apps.get_model('contenido', 'Temario')
    Mundo = apps.get_model('contenido', 'Mundo')
    Crucigrama = apps.get_model('crucigrama', 'Crucigrama')
    PalabraCrucigrama = apps.get_model('crucigrama', 'PalabraCrucigrama')

    # Buscar temario adecuado (de Casos de Uso si existe, o del Mundo 2, o el primero)
    temario = (
        Temario.objects.filter(nombre__icontains="caso").first()
        or Temario.objects.filter(mundo__orden=2).first()
        or Temario.objects.first()
    )

    if not temario:
        mundo = Mundo.objects.filter(orden=2).first() or Mundo.objects.create(
            nombre="Mundo 2: Casos de Uso", orden=2
        )
        temario = Temario.objects.create(
            mundo=mundo, nombre="Unidad 1: Conceptos de Casos de Uso", orden=1
        )

    orden_siguiente = Actividad.objects.filter(temario=temario).count() + 1

    actividad, _ = Actividad.objects.get_or_create(
        tipo="crucigrama",
        defaults={
            "temario": temario,
            "titulo": "Crucigrama: Casos de uso",
            "orden": orden_siguiente,
            "puntos_max": 100,
        }
    )

    crucigrama, _ = Crucigrama.objects.get_or_create(
        actividad=actividad,
        defaults={
            "filas": 13,
            "columnas": 10,
            "tiempo_limite_seg": 180,
        }
    )

    # Limpiar palabras anteriores para evitar duplicados
    PalabraCrucigrama.objects.filter(crucigrama=crucigrama).delete()

    palabras = [
        {
            "numero": 1,
            "direccion": "v",
            "fila_inicio": 0,
            "columna_inicio": 0,
            "respuesta": "EXTEND",
            "enunciado": "Relación en la que un caso de uso opcional amplía el comportamiento de otro caso de uso base (término en inglés).",
            "explicacion": "«Extend» indica que un caso de uso puede ampliar a otro solo bajo cierta condición; por ejemplo, “Usar pista” extiende “Resolver crucigrama”.",
        },
        {
            "numero": 2,
            "direccion": "v",
            "fila_inicio": 0,
            "columna_inicio": 7,
            "respuesta": "INCLUDE",
            "enunciado": "Relación en la que un caso de uso siempre incorpora el comportamiento de otro; sirve para reutilizar pasos (término en inglés).",
            "explicacion": "«Include» se usa cuando un caso de uso siempre incorpora a otro, para reutilizar pasos comunes como “Iniciar sesión”.",
        },
        {
            "numero": 3,
            "direccion": "v",
            "fila_inicio": 1,
            "columna_inicio": 3,
            "respuesta": "EXCEPCION",
            "enunciado": "Situación de error que impide continuar la ejecución normal del caso de uso.",
            "explicacion": "La excepción es un error o falla que impide continuar el caso de uso, como no poder cargar el crucigrama.",
        },
        {
            "numero": 4,
            "direccion": "v",
            "fila_inicio": 1,
            "columna_inicio": 9,
            "respuesta": "ACTOR",
            "enunciado": "Persona o sistema externo que interactúa con el sistema para lograr un objetivo.",
            "explicacion": "El actor es quien interactúa con SoftQuest para lograr un objetivo; en esta actividad, el Jugador.",
        },
        {
            "numero": 5,
            "direccion": "h",
            "fila_inicio": 5,
            "columna_inicio": 0,
            "respuesta": "DISPARADOR",
            "enunciado": "Evento que inicia la ejecución de un caso de uso.",
            "explicacion": "El disparador es el evento que inicia el caso de uso, por ejemplo cuando el jugador selecciona la actividad en el temario.",
        },
        {
            "numero": 6,
            "direccion": "v",
            "fila_inicio": 5,
            "columna_inicio": 5,
            "respuesta": "ROL",
            "enunciado": "Papel que una persona desempeña frente al sistema (ej. Jugador, Administrador).",
            "explicacion": "Un rol es el papel que una persona desempeña frente al sistema; define lo que puede hacer en él.",
        },
        {
            "numero": 7,
            "direccion": "v",
            "fila_inicio": 8,
            "columna_inicio": 8,
            "respuesta": "FLUJO",
            "enunciado": "Secuencia ordenada de pasos entre actor y sistema dentro de un caso de uso.",
            "explicacion": "El flujo es la secuencia ordenada de pasos entre actor y sistema; puede ser normal, alternativo o de excepción.",
        },
        {
            "numero": 8,
            "direccion": "h",
            "fila_inicio": 9,
            "columna_inicio": 3,
            "respuesta": "NORMAL",
            "enunciado": "Dicho del camino principal y esperado, sin errores ni desvíos.",
            "explicacion": "El flujo normal es el camino principal y esperado del caso de uso, cuando todo sale bien.",
        },
    ]

    for p in palabras:
        PalabraCrucigrama.objects.create(
            crucigrama=crucigrama,
            numero=p["numero"],
            direccion=p["direccion"],
            fila_inicio=p["fila_inicio"],
            columna_inicio=p["columna_inicio"],
            respuesta=p["respuesta"],
            enunciado=p["enunciado"],
            explicacion=p["explicacion"],
        )


def revertir_datos_iniciales_crucigrama(apps, schema_editor):
    Actividad = apps.get_model('contenido', 'Actividad')
    Actividad.objects.filter(tipo="crucigrama").delete()


class Migration(migrations.Migration):

    dependencies = [
        ('crucigrama', '0001_initial'),
        ('contenido', '0004_insignia_insigniausuario'),
    ]

    operations = [
        migrations.RunPython(crear_datos_iniciales_crucigrama, revertir_datos_iniciales_crucigrama),
    ]
