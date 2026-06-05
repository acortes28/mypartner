from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finances', '0005_tarjeta_movimiento_tarjeta'),
    ]

    operations = [
        migrations.AddField(
            model_name='movimiento',
            name='cuotas',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
    ]
