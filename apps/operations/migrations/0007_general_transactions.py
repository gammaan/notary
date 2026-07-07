# Generated manually for general (non-matter) transactions

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("operations", "0006_client_sex"),
    ]

    operations = [
        migrations.AddField(
            model_name="transaction",
            name="category",
            field=models.CharField(
                blank=True,
                choices=[
                    ("rent", "Rent"),
                    ("utilities", "Utilities"),
                    ("internet", "Internet"),
                    ("salary", "Salary"),
                    ("office_supplies", "Office supplies"),
                    ("other_income", "Other income"),
                    ("interest", "Interest"),
                    ("refund", "Refund"),
                    ("other", "Other"),
                ],
                max_length=32,
                verbose_name="category",
            ),
        ),
        migrations.AlterField(
            model_name="transaction",
            name="matter",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="transactions",
                to="operations.matter",
                verbose_name="matter",
            ),
        ),
    ]
