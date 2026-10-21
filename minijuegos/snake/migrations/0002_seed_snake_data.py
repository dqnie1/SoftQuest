from django.db import migrations


def crear_datos_iniciales_snake(apps, schema_editor):
    Actividad = apps.get_model('contenido', 'Actividad')
    Temario = apps.get_model('contenido', 'Temario')
    Snake = apps.get_model('snake', 'Snake')
    NivelSnake = apps.get_model('snake', 'NivelSnake')
    ItemNivel = apps.get_model('snake', 'ItemNivel')

    # Buscar temario adecuado (de requerimientos si existe, o el primero)
    temario = Temario.objects.filter(id=3).first() or Temario.objects.first()
    if not temario:
        return

    orden_siguiente = Actividad.objects.filter(temario=temario).count() + 1

    actividad, _ = Actividad.objects.get_or_create(
        tipo="snake",
        defaults={
            "temario": temario,
            "titulo": "Snake: Cazador de Requerimientos",
            "orden": orden_siguiente,
            "puntos_max": 100,
        }
    )

    snake, _ = Snake.objects.get_or_create(actividad=actividad)

    nivel, _ = NivelSnake.objects.get_or_create(
        snake=snake,
        numero=1,
        defaults={
            "titulo": "Identificación de RNF vs RF",
            "tema": "Ingeniería de Requerimientos",
            "instrucciones": (
                "Controla a la serpiente para recolectar todos los Requerimientos No Funcionales (RNF) "
                "del sistema. Evita los Requerimientos Funcionales (RF), ya que actuarán como obstáculos "
                "y terminarán la partida si los consumes."
            ),
            "filas": 20,
            "columnas": 20,
            "velocidad_ms": 180,
        }
    )

    # Limpiar items anteriores si existen para asegurar consistencia
    ItemNivel.objects.filter(nivel=nivel).delete()

    items = [
        # --- RNF (Objetivos: True) ---
        {
            "identificador": "RNF-01",
            "categoria": "Rendimiento",
            "texto": "El sistema debe procesar las consultas de búsqueda en menos de 1.5 segundos bajo una carga de 500 usuarios concurrentes.",
            "es_objetivo": True,
            "explicacion": "Es un Requisito No Funcional de Rendimiento porque impone una restricción cuantitativa y medible sobre el tiempo de respuesta del sistema.",
            "contraste": "",
        },
        {
            "identificador": "RNF-02",
            "categoria": "Seguridad",
            "texto": "Todas las contraseñas de los usuarios deben ser almacenadas utilizando un algoritmo de hash criptográfico seguro (Argon2 o bcrypt) con salting.",
            "es_objetivo": True,
            "explicacion": "Es un Requisito No Funcional de Seguridad porque establece una restricción técnica sobre cómo debe protegerse la información sensible.",
            "contraste": "",
        },
        {
            "identificador": "RNF-03",
            "categoria": "Disponibilidad",
            "texto": "La plataforma debe mantener una tasa de operatividad del 99.9% durante las horas hábiles de la institución.",
            "es_objetivo": True,
            "explicacion": "Es un Requisito No Funcional de Disponibilidad y Fiabilidad, ya que define el porcentaje de tiempo que el servicio debe estar accesible sin fallos.",
            "contraste": "",
        },
        {
            "identificador": "RNF-04",
            "categoria": "Usabilidad",
            "texto": "La interfaz debe cumplir con el nivel AA de las pautas WCAG 2.1 para garantizar la accesibilidad a usuarios con discapacidades.",
            "es_objetivo": True,
            "explicacion": "Es un Requisito No Funcional de Usabilidad y Accesibilidad, ya que define estándares de calidad para la interacción de cualquier usuario.",
            "contraste": "",
        },

        # --- RF (Obstáculos: False) ---
        {
            "identificador": "RF-01",
            "categoria": "Gestión de Cuentas",
            "texto": "El sistema permitirá al estudiante registrarse ingresando su matrícula, nombre completo, correo institucional y contraseña.",
            "es_objetivo": False,
            "explicacion": "Describe una función específica que el usuario puede realizar: la creación de una cuenta en el sistema.",
            "contraste": "Los Requerimientos Funcionales definen 'QUÉ' hace el software (servicios o funciones específicas), mientras que los RNF definen 'CÓMO' se comporta (atributos de calidad).",
        },
        {
            "identificador": "RF-02",
            "categoria": "Generación de Reportes",
            "texto": "El sistema generará un reporte descargable en formato PDF con el historial de calificaciones y avance de cada alumno.",
            "es_objetivo": False,
            "explicacion": "Describe una acción o salida que el sistema debe ejecutar ante una solicitud del usuario (generar un reporte en PDF).",
            "contraste": "Es una capacidad operativa del software (RF), no una restricción técnica ni un atributo de calidad (RNF).",
        },
        {
            "identificador": "RF-03",
            "categoria": "Notificaciones",
            "texto": "El sistema enviará un correo electrónico de confirmación al usuario cada vez que complete una actividad del curso.",
            "es_objetivo": False,
            "explicacion": "Describe un comportamiento funcional que el sistema ejecuta automáticamente ante un evento específico.",
            "contraste": "Indica una acción que el sistema realiza (RF), a diferencia del rendimiento, seguridad o confiabilidad del canal de envío (RNF).",
        },
    ]

    for item_data in items:
        ItemNivel.objects.create(
            nivel=nivel,
            identificador=item_data["identificador"],
            categoria=item_data["categoria"],
            texto=item_data["texto"],
            es_objetivo=item_data["es_objetivo"],
            explicacion=item_data["explicacion"],
            contraste=item_data["contraste"],
        )


def revertir_datos_iniciales_snake(apps, schema_editor):
    Actividad = apps.get_model('contenido', 'Actividad')
    Actividad.objects.filter(tipo="snake").delete()


class Migration(migrations.Migration):

    dependencies = [
        ('snake', '0001_initial'),
        ('contenido', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(crear_datos_iniciales_snake, revertir_datos_iniciales_snake),
    ]
