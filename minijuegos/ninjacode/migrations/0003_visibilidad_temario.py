from django.db import migrations


def mostrar_en_temario(apps, schema_editor):
    Actividad = apps.get_model('contenido', 'Actividad')
    for actividad in Actividad.objects.filter(tipo='ninjacode', orden__gte=90):
        ordenes = list(
            Actividad.objects.filter(temario_id=actividad.temario_id, orden__lt=90)
            .exclude(pk=actividad.pk)
            .values_list('orden', flat=True)
        )
        actividad.orden = (max(ordenes) + 1) if ordenes else 1
        actividad.save(update_fields=['orden'])


class Migration(migrations.Migration):

    dependencies = [
        ('ninjacode', '0002_sembrar_ninjacode'),
    ]

    operations = [
        migrations.RunPython(mostrar_en_temario, migrations.RunPython.noop),
    ]
