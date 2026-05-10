from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("store", "0022_order_tracking_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="estimated_delivery_time",
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
    ]
