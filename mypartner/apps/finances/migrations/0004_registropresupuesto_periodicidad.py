from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finances', '0003_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='registropresupuesto',
            name='periodicidad',
            field=models.CharField(
                choices=[('Puntual', 'Puntual'), ('Mensual', 'Mensual'), ('Anual', 'Anual')],
                default='Puntual',
                max_length=10,
            ),
        ),
    ]
