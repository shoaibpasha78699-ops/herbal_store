from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("store", "0015_alter_review_unique_together_order_is_paid_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="order",
            name="status",
            field=models.CharField(
                choices=[
                    ("Pending", "Pending"),
                    ("Paid", "Paid"),
                    ("Shipped", "Shipped"),
                    ("Delivered", "Delivered"),
                ],
                default="Pending",
                max_length=20,
            ),
        ),
    ]
