from django.db import migrations, models


def combine_client_names(apps, schema_editor):
    Client = apps.get_model("operations", "Client")
    for client in Client.objects.all():
        client.full_name = f"{client.first_name} {client.last_name}".strip()
        client.save(update_fields=["full_name"])


class Migration(migrations.Migration):

    dependencies = [
        ("operations", "0003_appointmentrequest_client_user"),
    ]

    operations = [
        migrations.AddField(
            model_name="client",
            name="full_name",
            field=models.CharField(max_length=300, null=True, verbose_name="full name"),
        ),
        migrations.RunPython(combine_client_names, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="client",
            name="full_name",
            field=models.CharField(max_length=300, verbose_name="full name"),
        ),
        migrations.RemoveField(
            model_name="client",
            name="first_name",
        ),
        migrations.RemoveField(
            model_name="client",
            name="last_name",
        ),
        migrations.AlterModelOptions(
            name="client",
            options={
                "ordering": ["full_name"],
                "verbose_name": "client",
                "verbose_name_plural": "clients",
            },
        ),
    ]
