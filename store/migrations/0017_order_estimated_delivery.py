from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("store", "0016_alter_order_status_choices"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="estimated_delivery",
            field=models.DateField(blank=True, null=True),
        ),
    ]
