import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finances', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='MetaAhorro',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('nombre', models.CharField(max_length=255)),
                ('monto_objetivo', models.PositiveIntegerField()),
                ('fecha_limite', models.DateField(blank=True, null=True)),
                ('tipo', models.CharField(choices=[('personal', 'Personal'), ('grupal', 'Grupal')], max_length=10)),
                ('activa', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('usuario', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='metas_ahorro',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('grupo', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='metas_ahorro',
                    to='groups.grupo',
                )),
            ],
            options={'db_table': 'metas_ahorro'},
        ),
        migrations.AddConstraint(
            model_name='metaahorro',
            constraint=models.CheckConstraint(
                condition=(
                    models.Q(usuario__isnull=False, grupo__isnull=True) |
                    models.Q(usuario__isnull=True, grupo__isnull=False)
                ),
                name='meta_ahorro_contexto_exclusivo',
            ),
        ),
        migrations.CreateModel(
            name='AporteAhorro',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('monto', models.IntegerField()),
                ('fecha', models.DateTimeField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('meta', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='aportes',
                    to='finances.metaahorro',
                )),
                ('usuario', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='aportes_ahorro',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={'db_table': 'aportes_ahorro'},
        ),
        migrations.AddIndex(
            model_name='aporteahorro',
            index=models.Index(fields=['meta', '-fecha'], name='idx_aporte_meta_fecha'),
        ),
    ]
