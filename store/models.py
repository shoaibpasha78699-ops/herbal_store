from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal


# CATEGORY
class Category(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


# PRODUCT
class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    stock = models.IntegerField(default=10)
    image = models.ImageField(upload_to="products/", null=True, blank=True)

    discount_percent = models.IntegerField(default=0)

    def discounted_price(self):
        if self.discount_percent > 0:
            discount = (self.price * Decimal(self.discount_percent)) / Decimal(100)
            return self.price - discount
        return self.price

    def __str__(self):
        return self.name


# ORDER
class Order(models.Model):
    PAYMENT_METHOD_COD = "COD"
    PAYMENT_METHOD_ONLINE = "ONLINE"
    PAYMENT_METHOD_CHOICES = [
        (PAYMENT_METHOD_COD, "Cash on Delivery"),
        (PAYMENT_METHOD_ONLINE, "Online"),
    ]

    STATUS_PENDING = "Pending"
    STATUS_PAID = "Paid"
    STATUS_SHIPPED = "Shipped"
    STATUS_OUT_FOR_DELIVERY = "Out for Delivery"
    STATUS_DELIVERED = "Delivered"
    STATUS_CANCELLED = "Cancelled"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_PAID, "Paid"),
        (STATUS_SHIPPED, "Shipped"),
        (STATUS_OUT_FOR_DELIVERY, "Out for Delivery"),
        (STATUS_DELIVERED, "Delivered"),
        (STATUS_CANCELLED, "Cancelled"),
    ]
    TRACKING_STATUS_PENDING = "Pending"
    TRACKING_STATUS_PAID = "Paid"
    TRACKING_STATUS_SHIPPED = "Shipped"
    TRACKING_STATUS_OUT_FOR_DELIVERY = "Out for Delivery"
    TRACKING_STATUS_DELIVERED = "Delivered"
    TRACKING_STATUS_CANCELLED = "Cancelled"
    TRACKING_STATUS_CHOICES = [
        (TRACKING_STATUS_PENDING, "Pending"),
        (TRACKING_STATUS_PAID, "Paid"),
        (TRACKING_STATUS_SHIPPED, "Shipped"),
        (TRACKING_STATUS_OUT_FOR_DELIVERY, "Out for Delivery"),
        (TRACKING_STATUS_DELIVERED, "Delivered"),
        (TRACKING_STATUS_CANCELLED, "Cancelled"),
    ]
    DEFAULT_TRACKING_LOCATIONS = {
        TRACKING_STATUS_PENDING: "Warehouse",
        TRACKING_STATUS_PAID: "Warehouse",
        TRACKING_STATUS_SHIPPED: "Main Transit Hub",
        TRACKING_STATUS_OUT_FOR_DELIVERY: "Local Delivery Center",
        TRACKING_STATUS_DELIVERED: "Delivered to your address",
        TRACKING_STATUS_CANCELLED: "Order Cancelled",
    }
    REFUND_NONE = "None"
    REFUND_PROCESSING = "Processing"
    REFUND_COMPLETED = "Completed"
    REFUND_STATUS_CHOICES = [
        (REFUND_NONE, "None"),
        (REFUND_PROCESSING, "Processing"),
        (REFUND_COMPLETED, "Completed"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=200)
    address = models.TextField()
    city = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(
        max_length=10,
        choices=PAYMENT_METHOD_CHOICES,
        default=PAYMENT_METHOD_COD,
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    tracking_status = models.CharField(
        max_length=50,
        choices=TRACKING_STATUS_CHOICES,
        default=TRACKING_STATUS_PENDING,
    )
    current_location = models.CharField(max_length=255, default="Warehouse")
    ordered_at = models.DateTimeField(auto_now_add=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    out_for_delivery_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    estimated_delivery = models.DateField(null=True, blank=True)
    estimated_delivery_time = models.CharField(max_length=20, blank=True, null=True)
    razorpay_order_id = models.CharField(max_length=200, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=200, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=500, blank=True, null=True)
    is_paid = models.BooleanField(default=False)
    cancel_reason = models.CharField(max_length=200, blank=True)
    cancel_comment = models.TextField(blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    refund_status = models.CharField(max_length=20, choices=REFUND_STATUS_CHOICES, default=REFUND_NONE)

    def clean(self):
        if (
            self.payment_method == self.PAYMENT_METHOD_ONLINE
            and self.status in [self.STATUS_PAID, self.STATUS_SHIPPED, self.STATUS_DELIVERED]
            and not self.razorpay_payment_id
        ):
            raise ValidationError("Online orders must be paid before shipping.")

        if self.payment_method == self.PAYMENT_METHOD_COD and self.status == self.STATUS_PAID:
            previous_status = None

            if self.pk:
                previous_status = (
                    Order.objects.filter(pk=self.pk)
                    .values_list("status", flat=True)
                    .first()
                )

            if previous_status not in [self.STATUS_DELIVERED, self.STATUS_PAID]:
                raise ValidationError("COD orders can be marked as paid only after delivery.")

    def _sync_tracking_status(self, previous_order):
        status_to_tracking = {
            self.STATUS_PENDING: self.TRACKING_STATUS_PENDING,
            self.STATUS_PAID: self.TRACKING_STATUS_PAID,
            self.STATUS_SHIPPED: self.TRACKING_STATUS_SHIPPED,
            self.STATUS_OUT_FOR_DELIVERY: self.TRACKING_STATUS_OUT_FOR_DELIVERY,
            self.STATUS_DELIVERED: self.TRACKING_STATUS_DELIVERED,
            self.STATUS_CANCELLED: self.TRACKING_STATUS_CANCELLED,
        }
        mapped_tracking_status = status_to_tracking.get(self.status)

        if not mapped_tracking_status:
            return set()

        changed_fields = set()

        if previous_order is None:
            if self.tracking_status != mapped_tracking_status:
                self.tracking_status = mapped_tracking_status
                changed_fields.add("tracking_status")
            return changed_fields

        if self.status != previous_order.status and self.tracking_status == previous_order.tracking_status:
            self.tracking_status = mapped_tracking_status
            changed_fields.add("tracking_status")

        return changed_fields

    def _update_tracking_details(self, previous_order):
        now = timezone.now()
        changed_fields = set()
        previous_location = previous_order.current_location if previous_order else None
        status_changed = previous_order is None or self.tracking_status != previous_order.tracking_status

        if status_changed:
            default_location = self.DEFAULT_TRACKING_LOCATIONS.get(
                self.tracking_status,
                self.DEFAULT_TRACKING_LOCATIONS[self.TRACKING_STATUS_PENDING],
            )
            if previous_order is None or self.current_location == previous_location:
                if self.current_location != default_location:
                    self.current_location = default_location
                    changed_fields.add("current_location")

        if self.tracking_status in [
            self.TRACKING_STATUS_SHIPPED,
            self.TRACKING_STATUS_OUT_FOR_DELIVERY,
            self.TRACKING_STATUS_DELIVERED,
        ] and not self.shipped_at:
            self.shipped_at = now
            changed_fields.add("shipped_at")

        if self.tracking_status in [
            self.TRACKING_STATUS_OUT_FOR_DELIVERY,
            self.TRACKING_STATUS_DELIVERED,
        ] and not self.out_for_delivery_at:
            self.out_for_delivery_at = now
            changed_fields.add("out_for_delivery_at")

        if self.tracking_status == self.TRACKING_STATUS_DELIVERED and not self.delivered_at:
            self.delivered_at = now
            changed_fields.add("delivered_at")

        return changed_fields

    def save(self, *args, **kwargs):
        previous_order = None
        if self.pk:
            previous_order = Order.objects.filter(pk=self.pk).first()

        auto_updated_fields = set()
        auto_updated_fields.update(self._sync_tracking_status(previous_order))
        auto_updated_fields.update(self._update_tracking_details(previous_order))

        update_fields = kwargs.get("update_fields")
        if update_fields is not None and auto_updated_fields:
            kwargs["update_fields"] = set(update_fields) | auto_updated_fields

        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order {self.id}"


# ORDER ITEM
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)


# REVIEW
class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


# OTP
class OTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)


# ADDRESS
class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="addresses")
    full_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20)
    address = models.TextField()
    city = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.full_name} - {self.city}"


# WISHLIST
class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="wishlist_items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="wishlisted_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "product")

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"
