from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("store", "0019_wishlist"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="cancel_comment",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="order",
            name="cancel_reason",
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name="order",
            name="cancelled_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="order",
            name="refund_status",
            field=models.CharField(
                choices=[
                    ("None", "None"),
                    ("Processing", "Processing"),
                    ("Completed", "Completed"),
                ],
                default="None",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="order",
            name="status",
            field=models.CharField(
                choices=[
                    ("Pending", "Pending"),
                    ("Paid", "Paid"),
                    ("Shipped", "Shipped"),
                    ("Delivered", "Delivered"),
                    ("Cancelled", "Cancelled"),
                ],
                default="Pending",
                max_length=20,
            ),
        ),
    ]
