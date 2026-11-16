import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenido', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CodeBreaker',
            fields=[
                ('actividad', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    primary_key=True,
                    related_name='codebreaker',
                    serialize=False,
                    to='contenido.actividad'
                )),
                ('filas', models.PositiveIntegerField(default=6)),
                ('columnas', models.PositiveIntegerField(default=10)),
                ('bloques_totales', models.PositiveIntegerField(default=60)),
                ('bloques_especiales', models.PositiveIntegerField(default=8)),
            ],
            options={
                'db_table': 'codebreaker',
            },
        ),
        migrations.CreateModel(
            name='ConceptoCodeBreaker',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('nombre', models.CharField(max_length=100)),
                ('nombre_corto', models.CharField(max_length=30)),
                ('tipo', models.CharField(
                    choices=[('positivo', 'Positivo'), ('negativo', 'Negativo')],
                    default='positivo',
                    max_length=20
                )),
                ('efecto_clave', models.CharField(max_length=30)),
                ('efecto_descripcion', models.CharField(max_length=255)),
                ('definicion', models.TextField()),
                ('explicacion', models.TextField()),
                ('tipo_ejemplo', models.CharField(default='Ejemplo', max_length=50)),
                ('ejemplo', models.TextField()),
                ('color', models.CharField(default='#5b5bf0', max_length=20)),
                ('codebreaker', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='conceptos',
                    to='codebreaker.codebreaker'
                )),
            ],
            options={
                'db_table': 'concepto_codebreaker',
                'ordering': ['id'],
            },
        ),
    ]
