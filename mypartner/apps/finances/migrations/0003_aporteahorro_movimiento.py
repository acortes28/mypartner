import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finances', '0002_metaahorro_aporteahorro'),
    ]

    operations = [
        migrations.AddField(
            model_name='aporteahorro',
            name='movimiento',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='aportes_ahorro',
                to='finances.movimiento',
            ),
        ),
    ]
