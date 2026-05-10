from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("store", "0021_order_payment_method"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="tracking_status",
            field=models.CharField(
                choices=[
                    ("Pending", "Pending"),
                    ("Paid", "Paid"),
                    ("Shipped", "Shipped"),
                    ("Out for Delivery", "Out for Delivery"),
                    ("Delivered", "Delivered"),
                    ("Cancelled", "Cancelled"),
                ],
                default="Pending",
                max_length=50,
            ),
        ),
        migrations.AddField(
            model_name="order",
            name="current_location",
            field=models.CharField(default="Warehouse", max_length=255),
        ),
        migrations.AddField(
            model_name="order",
            name="ordered_at",
            field=models.DateTimeField(default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="order",
            name="shipped_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="order",
            name="out_for_delivery_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="order",
            name="delivered_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
