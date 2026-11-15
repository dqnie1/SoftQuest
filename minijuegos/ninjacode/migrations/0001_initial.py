from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenido', '0004_insignia_insigniausuario'),
    ]

    operations = [
        migrations.CreateModel(
            name='NinjaCode',
            fields=[
                ('actividad', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    primary_key=True,
                    related_name='ninjacode',
                    serialize=False,
                    to='contenido.actividad',
                )),
            ],
            options={
                'db_table': 'ninjacode',
            },
        ),
        migrations.CreateModel(
            name='RequisitoNinja',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('texto', models.CharField(max_length=500)),
                ('tipo', models.CharField(
                    choices=[('FUNCIONAL', 'Funcional'), ('NO_FUNCIONAL', 'No funcional')],
                    max_length=20,
                )),
                ('ninjacode', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='requisitos',
                    to='ninjacode.ninjacode',
                )),
            ],
            options={
                'db_table': 'requisito_ninja',
            },
        ),
    ]
