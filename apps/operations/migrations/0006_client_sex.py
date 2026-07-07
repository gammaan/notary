from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("operations", "0005_uuid_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="client",
            name="sex",
            field=models.CharField(
                blank=True,
                choices=[("male", "Male"), ("female", "Female")],
                max_length=10,
                verbose_name="sex",
            ),
        ),
    ]
