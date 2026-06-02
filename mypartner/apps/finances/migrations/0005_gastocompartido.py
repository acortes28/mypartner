import uuid
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finances', '0004_registropresupuesto_periodicidad'),
        ('groups', '__first__'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='GastoCompartido',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('monto_pendiente', models.PositiveIntegerField()),
                ('pagado', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('grupo', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='gastos_compartidos', to='groups.grupo')),
                ('movimiento', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='compartidos', to='finances.movimiento')),
                ('usuario_acreedor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='gastos_acreedor', to=settings.AUTH_USER_MODEL)),
                ('usuario_deudor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='gastos_deudor', to=settings.AUTH_USER_MODEL)),
            ],
            options={'db_table': 'gastos_compartidos'},
        ),
    ]
