from django.db import migrations


def sembrar(apps, schema_editor):
    Actividad = apps.get_model('contenido', 'Actividad')
    Temario = apps.get_model('contenido', 'Temario')
    CubeCode = apps.get_model('cubecode', 'CubeCode')
    Nivel = apps.get_model('cubecode', 'NivelCubeCode')
    Ejercicio = apps.get_model('cubecode', 'EjercicioCubeCode')
    Bloque = apps.get_model('cubecode', 'BloqueCubeCode')

    from minijuegos.cubecode.datos import NIVELES

    actividad = Actividad.objects.filter(tipo='cubecode').first()
    if actividad is None:
        temario = (
            Temario.objects.filter(pk=2).first()
            or Temario.objects.order_by('mundo__orden', 'orden').first()
        )
        if temario is None:
            return
        ordenes = list(
            Actividad.objects.filter(temario=temario).values_list('orden', flat=True)
        )
        actividad = Actividad.objects.create(
            temario=temario,
            tipo='cubecode',
            titulo='CubeCode',
            orden=(max(ordenes) + 1) if ordenes else 1,
            puntos_max=100,
        )

    cubecode, _ = CubeCode.objects.get_or_create(actividad=actividad)
    if Nivel.objects.filter(cubecode=cubecode).exists():
        return

    for nivel_data in NIVELES:
        nivel = Nivel.objects.create(
            cubecode=cubecode,
            numero=nivel_data['numero'],
            nombre=nivel_data['nombre'],
        )
        for ejercicio_data in nivel_data['ejercicios']:
            ejercicio = Ejercicio.objects.create(
                nivel=nivel,
                numero=ejercicio_data['numero'],
                titulo=ejercicio_data['titulo'],
                objetivo=ejercicio_data['objetivo'],
            )
            for bloque in ejercicio_data['bloques']:
                Bloque.objects.create(
                    ejercicio=ejercicio,
                    texto=bloque['texto'],
                    orden_solucion=bloque['orden'],
                    pista=bloque['pista'],
                )


class Migration(migrations.Migration):

    dependencies = [
        ('cubecode', '0001_initial'),
        ('contenido', '0003_move_usuario_to_login'),
    ]

    operations = [
        migrations.RunPython(sembrar, migrations.RunPython.noop),
    ]
