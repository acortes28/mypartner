from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('finances', '0003_aporteahorro_movimiento'),
    ]

    operations = [
        migrations.AlterField(
            model_name='gastocompartido',
            name='movimiento',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='compartidos',
                to='finances.movimiento',
            ),
        ),
    ]
