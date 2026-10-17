from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contenido', '0002_usuario_cuenta'),
        ('login', '0001_initial'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AlterField(
                    model_name='progresoactividad',
                    name='usuario',
                    field=models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='progresos_actividad',
                        to='login.usuario',
                    ),
                ),
                migrations.AlterField(
                    model_name='progresousuario',
                    name='usuario',
                    field=models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='progreso',
                        to='login.usuario',
                    ),
                ),
                migrations.DeleteModel(
                    name='Usuario',
                ),
            ],
        ),
    ]
