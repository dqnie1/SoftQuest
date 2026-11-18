from django.db import migrations


def sembrar_sopaletras(apps, schema_editor):
    Actividad = apps.get_model('contenido', 'Actividad')
    Temario = apps.get_model('contenido', 'Temario')
    Mundo = apps.get_model('contenido', 'Mundo')
    SopaLetras = apps.get_model('sopaletras', 'SopaLetras')
    PalabraSopa = apps.get_model('sopaletras', 'PalabraSopa')
    from minijuegos.sopaletras.datos import PALABRAS_SOPALETRAS

    temario = (
        Temario.objects.filter(nombre__icontains="concepto").first()
        or Temario.objects.filter(mundo__orden=1).first()
        or Temario.objects.first()
    )

    if not temario:
        mundo = Mundo.objects.filter(orden=1).first() or Mundo.objects.create(
            nombre="Mundo 1: Fundamentos", orden=1
        )
        temario = Temario.objects.create(
            mundo=mundo, nombre="Unidad 1: Fundamentos de Software", orden=1
        )

    actividad = Actividad.objects.filter(tipo="sopaletras").first()
    if actividad is None:
        ordenes = list(
            Actividad.objects.filter(temario=temario, orden__lt=90).values_list('orden', flat=True)
        )
        siguiente_orden = (max(ordenes) + 1) if ordenes else 1
        actividad = Actividad.objects.create(
            temario=temario,
            tipo="sopaletras",
            titulo="Sopa de Letras: Conceptos de Software",
            orden=siguiente_orden,
            puntos_max=100,
        )

    sopa, _ = SopaLetras.objects.get_or_create(
        actividad=actividad,
        defaults={
            "dimension": 12,
            "total_palabras": 8,
        }
    )

    if PalabraSopa.objects.filter(sopaletras=sopa).exists():
        return

    for p in PALABRAS_SOPALETRAS:
        PalabraSopa.objects.create(
            sopaletras=sopa,
            palabra=p["palabra"],
            nombre=p["nombre"],
            definicion=p["definicion"],
            explicacion=p["explicacion"],
            tipo_ejemplo=p.get("tipo_ejemplo", "Ejemplo"),
            ejemplo=p["ejemplo"],
            color=p.get("color", "#818cf8"),
        )


class Migration(migrations.Migration):

    dependencies = [
        ('sopaletras', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(sembrar_sopaletras, migrations.RunPython.noop),
    ]
