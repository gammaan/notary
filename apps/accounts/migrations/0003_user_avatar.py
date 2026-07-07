from django.db import migrations, models

import accounts.validators


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_alter_user_role"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="avatar",
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to="avatars/%Y/%m/",
                validators=[accounts.validators.validate_avatar_upload],
                verbose_name="profile photo",
            ),
        ),
    ]
