import ham.models
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("ham", "0003_seed_network")]

    operations = [
        migrations.AlterField(
            model_name="humanasset",
            name="portrait",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="humanasset",
            name="uploaded_portrait",
            field=models.ImageField(
                blank=True,
                upload_to=ham.models.human_asset_portrait_upload_path,
            ),
        ),
    ]
