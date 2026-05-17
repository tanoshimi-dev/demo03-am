from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="accountsession",
            name="source",
            field=models.CharField(
                choices=[
                    ("dev-header", "Dev header"),
                    ("portal-header", "Portal header"),
                    ("portal-jwt", "Portal JWT cookie"),
                ],
                max_length=20,
            ),
        ),
    ]
