from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('booking', '0003_delete_customerfeedback'),
    ]

    operations = [
        # Fix the PopularRoute decimal fields
        migrations.AlterField(
            model_name='popularroute',
            name='distance_km',
            field=models.DecimalField(decimal_places=2, max_digits=5),
        ),
        migrations.AlterField(
            model_name='popularroute',
            name='rate',
            field=models.DecimalField(decimal_places=2, max_digits=6),
        ),
    ]
