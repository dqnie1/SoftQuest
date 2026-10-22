from django.db import migrations


def quitar_cuartos(apps, schema_editor):
    Ejercicio = apps.get_model('cubecode', 'EjercicioCubeCode')
    Progreso = apps.get_model('cubecode', 'ProgresoCubeCode')
    ProgresoActividad = apps.get_model('contenido', 'ProgresoActividad')

    sobrantes = set(Ejercicio.objects.filter(numero__gt=3).values_list('id', flat=True))
    Ejercicio.objects.filter(numero__gt=3).delete()

    for progreso in Progreso.objects.all():
        hechos = [
            int(item)
            for item in (progreso.ejercicios_hechos or [])
            if int(item) not in sobrantes
        ]
        total = Ejercicio.objects.filter(nivel__cubecode_id=progreso.cubecode_id).count()
        if hechos and total and len(hechos) >= total:
            puntaje = 100
        elif hechos and total:
            puntaje = (len(hechos) * 100) // total
        else:
            puntaje = 0
        progreso.ejercicios_hechos = hechos
        progreso.puntaje = puntaje
        progreso.save(update_fields=['ejercicios_hechos', 'puntaje'])
        ProgresoActividad.objects.filter(
            usuario_id=progreso.usuario_id,
            actividad_id=progreso.cubecode_id,
        ).update(
            puntaje=puntaje,
            estado='completado' if total and len(hechos) >= total else 'en_progreso',
        )


class Migration(migrations.Migration):

    dependencies = [
        ('cubecode', '0003_facilitar_ejercicios'),
    ]

    operations = [
        migrations.RunPython(quitar_cuartos, migrations.RunPython.noop),
    ]
