from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenido', '0002_usuario_cuenta'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.CreateModel(
                    name='Usuario',
                    fields=[
                        ('id', models.AutoField(primary_key=True, serialize=False)),
                        ('nombre', models.CharField(max_length=100)),
                        ('email', models.EmailField(max_length=254)),
                        (
                            'cuenta',
                            models.OneToOneField(
                                blank=True,
                                null=True,
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name='perfil_contenido',
                                to=settings.AUTH_USER_MODEL,
                            ),
                        ),
                    ],
                    options={
                        'db_table': 'usuario',
                    },
                ),
            ],
        ),
    ]
