# Generated migration to add BLOB fields for images
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0008_alter_cartype_rate_per_km_alter_inquiry_distance_km_and_more'),
    ]

    operations = [
        # Add BLOB fields for Car images
        migrations.AddField(
            model_name='car',
            name='image_data',
            field=models.BinaryField(blank=True, null=True, help_text='Binary image data'),
        ),
        migrations.AddField(
            model_name='car',
            name='image_filename',
            field=models.CharField(max_length=255, blank=True, null=True, help_text='Original filename'),
        ),
        migrations.AddField(
            model_name='car',
            name='image_content_type',
            field=models.CharField(max_length=100, blank=True, null=True, help_text='Image MIME type'),
        ),
        
        # Add BLOB fields for PopularRoute images
        migrations.AddField(
            model_name='popularroute',
            name='image_data',
            field=models.BinaryField(blank=True, null=True, help_text='Binary image data'),
        ),
        migrations.AddField(
            model_name='popularroute',
            name='image_filename',
            field=models.CharField(max_length=255, blank=True, null=True, help_text='Original filename'),
        ),
        migrations.AddField(
            model_name='popularroute',
            name='image_content_type',
            field=models.CharField(max_length=100, blank=True, null=True, help_text='Image MIME type'),
        ),
    ]
