import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenido', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SopaLetras',
            fields=[
                ('actividad', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    primary_key=True,
                    related_name='sopaletras',
                    serialize=False,
                    to='contenido.actividad'
                )),
                ('dimension', models.PositiveIntegerField(default=12)),
                ('total_palabras', models.PositiveIntegerField(default=8)),
            ],
            options={
                'db_table': 'sopa_letras',
            },
        ),
        migrations.CreateModel(
            name='PalabraSopa',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('palabra', models.CharField(max_length=50)),
                ('nombre', models.CharField(max_length=50)),
                ('definicion', models.TextField()),
                ('explicacion', models.TextField()),
                ('tipo_ejemplo', models.CharField(default='Ejemplo', max_length=50)),
                ('ejemplo', models.TextField()),
                ('color', models.CharField(default='#818cf8', max_length=20)),
                ('sopaletras', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='palabras',
                    to='sopaletras.sopaletras'
                )),
            ],
            options={
                'db_table': 'palabra_sopa',
                'ordering': ['id'],
            },
        ),
    ]
