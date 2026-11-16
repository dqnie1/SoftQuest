from django.db import migrations


def sembrar_codebreaker(apps, schema_editor):
    Actividad = apps.get_model('contenido', 'Actividad')
    Temario = apps.get_model('contenido', 'Temario')
    Mundo = apps.get_model('contenido', 'Mundo')
    CodeBreaker = apps.get_model('codebreaker', 'CodeBreaker')
    ConceptoCodeBreaker = apps.get_model('codebreaker', 'ConceptoCodeBreaker')
    from minijuegos.codebreaker.datos import CONCEPTOS_CODEBREAKER

    # Buscar temario adecuado (de pruebas/calidad o del Mundo 2 o primero disponible)
    temario = (
        Temario.objects.filter(nombre__icontains="prueba").first()
        or Temario.objects.filter(nombre__icontains="calidad").first()
        or Temario.objects.filter(mundo__orden=2).first()
        or Temario.objects.first()
    )

    if not temario:
        mundo = Mundo.objects.filter(orden=1).first() or Mundo.objects.create(
            nombre="Mundo 1: Fundamentos", orden=1
        )
        temario = Temario.objects.create(
            mundo=mundo, nombre="Unidad 1: Fundamentos de Software", orden=1
        )

    actividad = Actividad.objects.filter(tipo="codebreaker").first()
    if actividad is None:
        ordenes = list(
            Actividad.objects.filter(temario=temario, orden__lt=90).values_list('orden', flat=True)
        )
        siguiente_orden = (max(ordenes) + 1) if ordenes else 1
        actividad = Actividad.objects.create(
            temario=temario,
            tipo="codebreaker",
            titulo="CodeBreaker: Rompebloques de Software",
            orden=siguiente_orden,
            puntos_max=100,
        )

    cb, _ = CodeBreaker.objects.get_or_create(
        actividad=actividad,
        defaults={
            "filas": 6,
            "columnas": 10,
            "bloques_totales": 60,
            "bloques_especiales": 8,
        }
    )

    # Si ya existen conceptos, no duplicar
    if ConceptoCodeBreaker.objects.filter(codebreaker=cb).exists():
        return

    for c in CONCEPTOS_CODEBREAKER:
        ConceptoCodeBreaker.objects.create(
            codebreaker=cb,
            nombre=c["nombre"],
            nombre_corto=c["nombre_corto"],
            tipo=c["tipo"],
            efecto_clave=c["efecto_clave"],
            efecto_descripcion=c["efecto_descripcion"],
            definicion=c["definicion"],
            explicacion=c["explicacion"],
            tipo_ejemplo=c.get("tipo_ejemplo", "Ejemplo"),
            ejemplo=c["ejemplo"],
            color=c.get("color", "#5b5bf0"),
        )


class Migration(migrations.Migration):

    dependencies = [
        ('codebreaker', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(sembrar_codebreaker, migrations.RunPython.noop),
    ]
