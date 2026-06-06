import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finances', '0004_gastocompartido_movimiento_nullable'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Tarjeta',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('nombre', models.CharField(max_length=100)),
                ('tipo', models.CharField(choices=[('Debito', 'Débito'), ('Credito', 'Crédito')], max_length=10)),
                ('banco', models.CharField(max_length=100)),
                ('cupo_total', models.PositiveIntegerField(blank=True, null=True)),
                ('cupo_usado', models.PositiveIntegerField(blank=True, null=True)),
                ('activa', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('usuario', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='tarjetas',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={'db_table': 'tarjetas'},
        ),
        migrations.AddField(
            model_name='movimiento',
            name='tarjeta',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='movimientos',
                to='finances.tarjeta',
            ),
        ),
    ]
