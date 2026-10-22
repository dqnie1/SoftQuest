from django.db import migrations


def expandir_tablero_y_poblar_datos(apps, schema_editor):
    NivelSnake = apps.get_model('snake', 'NivelSnake')
    ItemNivel = apps.get_model('snake', 'ItemNivel')

    # Actualizar todos los niveles existentes a 26x26
    for nivel in NivelSnake.objects.all():
        nivel.filas = 26
        nivel.columnas = 26
        nivel.velocidad_ms = 170
        nivel.save()

    nivel_1 = NivelSnake.objects.first()
    if not nivel_1:
        return

    # Limpiar ítems previos para repoblar con la colección completa expandida
    ItemNivel.objects.filter(nivel=nivel_1).delete()

    items = [
        # =====================================================================
        # 8 REQUERIMIENTOS NO FUNCIONALES (RNF - Objetivos: True)
        # =====================================================================
        {
            "identificador": "RNF-01",
            "categoria": "Rendimiento",
            "texto": "El sistema debe procesar las consultas de búsqueda en menos de 1.5 segundos bajo una carga de 500 usuarios concurrentes.",
            "es_objetivo": True,
            "explicacion": "Es un Requisito No Funcional de Rendimiento porque impone una restricción cuantitativa y medible sobre el tiempo de respuesta del sistema bajo carga.",
            "contraste": "",
        },
        {
            "identificador": "RNF-02",
            "categoria": "Seguridad",
            "texto": "Todas las contraseñas de los usuarios deben ser almacenadas utilizando un algoritmo de hash criptográfico seguro (Argon2 o bcrypt) con salt aleatorio de 128 bits.",
            "es_objetivo": True,
            "explicacion": "Es un Requisito No Funcional de Seguridad porque establece una restricción técnica y arquitectónica sobre cómo debe protegerse la información confidencial.",
            "contraste": "",
        },
        {
            "identificador": "RNF-03",
            "categoria": "Disponibilidad",
            "texto": "La plataforma debe mantener una tasa de disponibilidad del 99.9% durante las horas hábiles de la institución (no más de 43 minutos de inactividad mensual).",
            "es_objetivo": True,
            "explicacion": "Es un Requisito No Funcional de Disponibilidad y Fiabilidad, ya que define el porcentaje de tiempo que el servicio debe estar en línea y operativo.",
            "contraste": "",
        },
        {
            "identificador": "RNF-04",
            "categoria": "Usabilidad",
            "texto": "La interfaz web debe cumplir con el nivel AA de las pautas WCAG 2.1 para garantizar la accesibilidad a personas con discapacidades visuales y motrices.",
            "es_objetivo": True,
            "explicacion": "Es un Requisito No Funcional de Usabilidad y Accesibilidad, ya que define estándares de calidad para la interacción de cualquier usuario independientemente de sus capacidades.",
            "contraste": "",
        },
        {
            "identificador": "RNF-05",
            "categoria": "Escalabilidad",
            "texto": "La arquitectura del backend debe soportar escalamiento horizontal automático para atender incrementos repentinos de hasta 10,000 peticiones por minuto.",
            "es_objetivo": True,
            "explicacion": "Es un Requisito No Funcional de Escalabilidad, pues especifica la capacidad del sistema para adaptarse dinámicamente a una demanda creciente sin degradar su rendimiento.",
            "contraste": "",
        },
        {
            "identificador": "RNF-06",
            "categoria": "Mantenibilidad",
            "texto": "El código fuente del sistema debe mantener una cobertura mínima de pruebas unitarias automatizadas del 80% y seguir la convención de estilo PEP 8.",
            "es_objetivo": True,
            "explicacion": "Es un Requisito No Funcional de Mantenibilidad y Calidad de Código, ya que facilita futuras extensiones, depuraciones y refactorizaciones seguras.",
            "contraste": "",
        },
        {
            "identificador": "RNF-07",
            "categoria": "Portabilidad",
            "texto": "La aplicación debe poder empaquetarse y ejecutarse sin modificaciones en contenedores Docker sobre servidores Linux (Ubuntu, Debian) y entornos cloud.",
            "es_objetivo": True,
            "explicacion": "Es un Requisito No Funcional de Portabilidad, pues garantiza que el software funcione de manera consistente en múltiples entornos operativos e infraestructuras.",
            "contraste": "",
        },
        {
            "identificador": "RNF-08",
            "categoria": "Confiabilidad",
            "texto": "El tiempo medio entre fallos (MTBF) del servicio principal de base de datos debe ser superior a 720 horas continuas de operación ininterrumpida.",
            "es_objetivo": True,
            "explicacion": "Es un Requisito No Funcional de Confiabilidad y Robustez, ya que establece una métrica cuantitativa de estabilidad operativa.",
            "contraste": "",
        },

        # =====================================================================
        # 8 REQUERIMIENTOS FUNCIONALES (RF - Obstáculos: False)
        # =====================================================================
        {
            "identificador": "RF-01",
            "categoria": "Gestión de Cuentas",
            "texto": "El sistema permitirá al estudiante registrarse ingresando su matrícula, nombre completo, correo institucional y contraseña.",
            "es_objetivo": False,
            "explicacion": "Describe una función directa que el usuario ejecuta: registrarse en la plataforma mediante un formulario.",
            "contraste": "Los Requerimientos Funcionales definen 'QUÉ' hace el software (acciones, transacciones), mientras que los RNF definen 'CÓMO' se comporta (calidad, restricciones).",
        },
        {
            "identificador": "RF-02",
            "categoria": "Generación de Reportes",
            "texto": "El sistema generará un reporte descargable en formato PDF con el historial de calificaciones y avance pedagógico de cada alumno.",
            "es_objetivo": False,
            "explicacion": "Describe una salida específica y un servicio proporcionado al usuario (exportar reporte PDF).",
            "contraste": "Es una capacidad operativa del sistema (RF), no una restricción sobre el rendimiento o seguridad del mismo (RNF).",
        },
        {
            "identificador": "RF-03",
            "categoria": "Notificaciones",
            "texto": "El sistema enviará un correo electrónico de confirmación al usuario cada vez que complete una actividad del curso.",
            "es_objetivo": False,
            "explicacion": "Describe una acción automatizada que el sistema realiza ante un evento de negocio (envío de email al completar reto).",
            "contraste": "Indica una funcionalidad específica (RF), a diferencia del tiempo de entrega o tasa de entrega del correo (RNF).",
        },
        {
            "identificador": "RF-04",
            "categoria": "Pasarela de Pagos",
            "texto": "El sistema debe permitir a los clientes realizar pagos mediante tarjeta de crédito, tarjeta de débito o PayPal.",
            "es_objetivo": False,
            "explicacion": "Representa un proceso transaccional que permite al usuario pagar por un curso o certificación.",
            "contraste": "Es una función del sistema (RF). La encriptación o el cumplimiento PCI-DSS del pago correspondería a un RNF.",
        },
        {
            "identificador": "RF-05",
            "categoria": "Carrito de Compras",
            "texto": "El usuario podrá agregar cursos al carrito de compras, modificar cantidades y eliminarlos antes de confirmar su orden.",
            "es_objetivo": False,
            "explicacion": "Es una interacción funcional de gestión de compras por parte del cliente dentro de la tienda virtual.",
            "contraste": "Define operaciones que el usuario realiza sobre entidades de datos (RF), no una restricción arquitectónica (RNF).",
        },
        {
            "identificador": "RF-06",
            "categoria": "Búsqueda y Filtrado",
            "texto": "El sistema proporcionará un buscador con filtros por categoría, nivel de dificultad y docente responsable.",
            "es_objetivo": False,
            "explicacion": "Es una herramienta de navegación y consulta ofrecida al usuario para localizar contenido.",
            "contraste": "El filtrado es una funcionalidad (RF). Que la búsqueda tarde menos de 1 segundo es el RNF asociado.",
        },
        {
            "identificador": "RF-07",
            "categoria": "Recuperación de Acceso",
            "texto": "El sistema permitirá al usuario solicitar un enlace temporal de restablecimiento de contraseña enviado a su correo registrado.",
            "es_objetivo": False,
            "explicacion": "Corresponde a un flujo de trabajo para restablecer credenciales de acceso olvidadas.",
            "contraste": "Describe una secuencia de pasos funcionales (RF). La caducidad o entropía del token es un RNF de seguridad.",
        },
        {
            "identificador": "RF-08",
            "categoria": "Gestión de Perfil",
            "texto": "El usuario podrá editar sus datos personales, subir una fotografía de avatar y configurar sus preferencias de notificación.",
            "es_objetivo": False,
            "explicacion": "Son acciones de administración de información del perfil del usuario en el sistema.",
            "contraste": "Representa pantallas y botones de acción (RF), mientras que el límite de tamaño de la imagen o compresión es un RNF.",
        },
    ]

    for item_data in items:
        ItemNivel.objects.create(
            nivel=nivel_1,
            identificador=item_data["identificador"],
            categoria=item_data["categoria"],
            texto=item_data["texto"],
            es_objetivo=item_data["es_objetivo"],
            explicacion=item_data["explicacion"],
            contraste=item_data["contraste"],
        )


def revertir_expansion(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('snake', '0002_seed_snake_data'),
    ]

    operations = [
        migrations.RunPython(expandir_tablero_y_poblar_datos, revertir_expansion),
    ]
