from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("store", "0020_order_cancellation_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="payment_method",
            field=models.CharField(
                choices=[("COD", "Cash on Delivery"), ("ONLINE", "Online")],
                default="COD",
                max_length=10,
            ),
        ),
    ]
