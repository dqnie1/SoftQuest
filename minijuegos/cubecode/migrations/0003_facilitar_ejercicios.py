from django.db import migrations


def actualizar(apps, schema_editor):
    CubeCode = apps.get_model('cubecode', 'CubeCode')
    Nivel = apps.get_model('cubecode', 'NivelCubeCode')
    Ejercicio = apps.get_model('cubecode', 'EjercicioCubeCode')
    Bloque = apps.get_model('cubecode', 'BloqueCubeCode')

    from minijuegos.cubecode.datos import NIVELES

    for cubecode in CubeCode.objects.all():
        for nivel_data in NIVELES:
            nivel = Nivel.objects.filter(cubecode=cubecode, numero=nivel_data['numero']).first()
            if nivel is None:
                nivel = Nivel.objects.create(
                    cubecode=cubecode,
                    numero=nivel_data['numero'],
                    nombre=nivel_data['nombre'],
                )
            for ejercicio_data in nivel_data['ejercicios']:
                ejercicio = Ejercicio.objects.filter(nivel=nivel, numero=ejercicio_data['numero']).first()
                if ejercicio is None:
                    ejercicio = Ejercicio.objects.create(
                        nivel=nivel,
                        numero=ejercicio_data['numero'],
                        titulo=ejercicio_data['titulo'],
                        objetivo=ejercicio_data['objetivo'],
                    )
                else:
                    ejercicio.titulo = ejercicio_data['titulo']
                    ejercicio.objetivo = ejercicio_data['objetivo']
                    ejercicio.save(update_fields=['titulo', 'objetivo'])
                Bloque.objects.filter(ejercicio=ejercicio).delete()
                for bloque in ejercicio_data['bloques']:
                    Bloque.objects.create(
                        ejercicio=ejercicio,
                        texto=bloque['texto'],
                        orden_solucion=bloque['orden'],
                        pista=bloque['pista'],
                    )


class Migration(migrations.Migration):

    dependencies = [
        ('cubecode', '0002_sembrar_cubecode'),
    ]

    operations = [
        migrations.RunPython(actualizar, migrations.RunPython.noop),
    ]
