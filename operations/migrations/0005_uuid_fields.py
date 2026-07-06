import uuid

from django.db import migrations, models


def populate_uuids(apps, schema_editor):
    for model_name in ("Client", "Matter", "Document", "Transaction", "AppointmentRequest"):
        Model = apps.get_model("operations", model_name)
        for row in Model.objects.all():
            row.uuid = uuid.uuid4()
            row.save(update_fields=["uuid"])


class Migration(migrations.Migration):

    dependencies = [
        ("operations", "0004_client_full_name"),
    ]

    operations = [
        migrations.AddField(
            model_name="client",
            name="uuid",
            field=models.UUIDField(db_index=True, editable=False, null=True, verbose_name="uuid"),
        ),
        migrations.AddField(
            model_name="matter",
            name="uuid",
            field=models.UUIDField(db_index=True, editable=False, null=True, verbose_name="uuid"),
        ),
        migrations.AddField(
            model_name="document",
            name="uuid",
            field=models.UUIDField(db_index=True, editable=False, null=True, verbose_name="uuid"),
        ),
        migrations.AddField(
            model_name="transaction",
            name="uuid",
            field=models.UUIDField(db_index=True, editable=False, null=True, verbose_name="uuid"),
        ),
        migrations.AddField(
            model_name="appointmentrequest",
            name="uuid",
            field=models.UUIDField(db_index=True, editable=False, null=True, verbose_name="uuid"),
        ),
        migrations.RunPython(populate_uuids, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="client",
            name="uuid",
            field=models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True, verbose_name="uuid"),
        ),
        migrations.AlterField(
            model_name="matter",
            name="uuid",
            field=models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True, verbose_name="uuid"),
        ),
        migrations.AlterField(
            model_name="document",
            name="uuid",
            field=models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True, verbose_name="uuid"),
        ),
        migrations.AlterField(
            model_name="transaction",
            name="uuid",
            field=models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True, verbose_name="uuid"),
        ),
        migrations.AlterField(
            model_name="appointmentrequest",
            name="uuid",
            field=models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True, verbose_name="uuid"),
        ),
    ]
