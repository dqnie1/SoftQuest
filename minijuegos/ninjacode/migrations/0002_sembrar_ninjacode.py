from django.db import migrations


def sembrar(apps, schema_editor):
    Actividad = apps.get_model('contenido', 'Actividad')
    Temario = apps.get_model('contenido', 'Temario')
    NinjaCode = apps.get_model('ninjacode', 'NinjaCode')
    RequisitoNinja = apps.get_model('ninjacode', 'RequisitoNinja')
    from minijuegos.ninjacode.datos import FUNCIONALES, NO_FUNCIONALES

    actividad = Actividad.objects.filter(tipo='ninjacode').first()
    if actividad is None:
        temario = (
            Temario.objects.filter(nombre__icontains='requer').first()
            or Temario.objects.filter(pk=2).first()
            or Temario.objects.order_by('mundo__orden', 'orden').first()
        )
        if temario is None:
            return
        ordenes = list(
            Actividad.objects.filter(temario=temario, orden__lt=90).values_list('orden', flat=True)
        )
        actividad = Actividad.objects.create(
            temario=temario,
            tipo='ninjacode',
            titulo='NinjaCode',
            orden=(max(ordenes) + 1) if ordenes else 1,
            puntos_max=100,
        )

    ninjacode, _ = NinjaCode.objects.get_or_create(actividad=actividad)
    if RequisitoNinja.objects.filter(ninjacode=ninjacode).exists():
        return
    for texto in FUNCIONALES:
        RequisitoNinja.objects.create(ninjacode=ninjacode, texto=texto, tipo='FUNCIONAL')
    for texto in NO_FUNCIONALES:
        RequisitoNinja.objects.create(ninjacode=ninjacode, texto=texto, tipo='NO_FUNCIONAL')


class Migration(migrations.Migration):

    dependencies = [
        ('ninjacode', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(sembrar, migrations.RunPython.noop),
    ]
