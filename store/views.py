import random
import json
from decimal import Decimal
from datetime import timedelta

import razorpay

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Q, Count, Sum, Avg, F, DecimalField, ExpressionWrapper

from .models import Product, Category, OTP, Order, OrderItem, Review, Address, Wishlist


SITE_KNOWLEDGE_SECTIONS = {
    "store_overview": """
Herbal Store is a Django-based ecommerce website focused on herbal wellness, personal care, Ayurvedic-style products,
herbal teas, natural supplements, essential oils, baby care, skincare, hair care, and immunity support. The website is
structured like a practical online shop rather than a brochure. A user can land on the home page, browse category sections,
search for products, open product detail pages, add items to cart, move toward checkout, save products in a wishlist, manage
addresses, view profile information, and track orders from purchase through delivery or cancellation. The store branding emphasizes
clean ingredients, natural wellness, confident shopping, secure ordering, and smoother support.

The main customer-facing navigation centers around home, search, cart, profile, wishlist, saved addresses, and order tracking.
When a customer is logged in, the website exposes more personalized actions like My Orders, Saved Addresses, Wishlist, and Profile.
When a customer is not logged in, they can still browse the catalog and product pages, but order tracking and wishlist usage become
more limited until login. The website also includes a support chat widget, and that chat should behave like a store-trained assistant
that understands the website layout, the shopping workflow, the catalog, and common support questions.

From a support point of view, the website is not only about products. It is also about answering practical shopping questions:
how many products exist, what categories are available, which product is currently being viewed, which items have discounts, what
checkout methods are supported, where to manage addresses, how to cancel orders, and what users can expect from delivery and tracking.
""".strip(),
    "catalog_and_products": """
The catalog is the heart of the website. Products are stored in the database with a name, category, price, description, stock count,
image, and optional discount percentage. The discounted price is computed dynamically from the original price and discount percent.
This means the support assistant should always be able to answer direct product questions such as current price, original price, discount
percentage, stock status, category name, and whether a product is available right now.

The product detail page presents a premium product view with a large product image, category badge, product name, rating summary, review
count, price block, availability status, description, stock information, and action buttons like Add to Cart and Continue Shopping.
The same page also supports reviews, so users can ask about ratings, reviews, what the product is, what the product is used for, and
whether it currently has any feedback. If a customer asks about "this product" while on a product page, the assistant should understand
that the question refers to the current page product and answer with the exact product context rather than a generic website description.

The home page and search experience also matter. Users can browse all products, filter by category through category links, and search
using a query string. A good site assistant should be able to describe products, suggest related items, identify likely matches from
user phrasing, and surface product suggestions when the query is about a concern like hair care, skin care, immunity, digestion, or baby care.
""".strip(),
    "categories_and_navigation": """
The website organizes products into categories such as Skin Care, herbal medicine, hair care, immunity boosters, Ayurvedic Medicines,
Herbal Teas, Personal Care, Weight Loss & Fitness, Baby Care, Essential Oils, and Natural Supplements. Category pages show only the
products that belong to that category. This means the chatbot should be able to answer category questions such as which categories exist,
which products belong to a category, how to browse a category, and where category links take the customer.

Navigation on the website is centered around practical shopping actions. The logo returns the user to the home page. The search bar routes
to the search results view. Cart opens the customer’s current session-based cart. Logged-in users can open the profile menu and navigate to
My Profile, My Orders, Wishlist, and Saved Addresses. If a user asks "where can I see my orders", "where do I manage my address", "where is
wishlist", or "what pages does this website have", the assistant should answer with clear page-level guidance rather than vague help text.

The website is not a content-heavy blog or marketing funnel; it is a store workflow. So the assistant should prioritize route-aware, page-aware,
and action-oriented guidance. When users ask how to do something, the assistant should explain the exact page or route involved: home for browsing,
search for discovery, product pages for details, cart for session items, checkout for payment, my-orders for tracking, my-address for saved address
management, profile for personal information, and wishlist for saved products.
""".strip(),
    "account_and_auth": """
Account handling on the website is simple and practical. Login is based on email OTP flow rather than a traditional password-first form inside
the current custom pages. A user enters an email address on the login page. If a user with that email does not exist, a user can be created in the
flow. An OTP is generated, emailed to the customer, and then verified on the verify-otp page. After successful verification, the user is logged in
and redirected to the home page. There is also a register page that supports username, email, password, and password confirmation for direct account creation.

From a support perspective, the assistant should know that login unlocks more personalized functions: tracking personal orders, storing addresses,
managing wishlist items, and updating profile information. If a user asks why they cannot track an order, save wishlist items, or see personal order
history, the assistant should explain that login is required for user-specific features. If the user asks how login works, the assistant should describe
the OTP flow clearly and mention the verify step.

The profile page lets users update their username and email. It also summarizes order counts, delivered order counts, address counts, wishlist counts,
and recent order information. So if someone asks what the profile page is for, the assistant should explain that it is the place for personal account
details and a high-level snapshot of activity on the store.
""".strip(),
    "cart_and_checkout": """
The cart on the website is session-based. Products are added with quantity management, and users can increase, decrease, or remove cart entries.
The cart page summarizes selected items and calculates totals based on discounted product prices where applicable. This means the assistant should
know how to answer questions like whether the cart belongs to the current session, how totals are calculated, whether discounts are already reflected,
and where to adjust quantities.

Checkout requires the user to be logged in. The checkout page uses the user’s default saved address when one exists. If no default address is found,
the page explicitly asks the customer to add one from Saved Addresses. The page supports two payment options: online payment via Razorpay and Cash on
Delivery. Online payment is started from the create-payment endpoint and finalized through verify-payment after the Razorpay callback. Cash on Delivery
creates the order directly with COD status handling.

A well-trained assistant should be able to explain the checkout flow step by step: review cart, ensure a default address exists, go to checkout, choose
online payment or Cash on Delivery, complete payment if paying online, and then review the order in My Orders. If a user asks whether online payment
is secure or what payment methods are available, the assistant should answer directly using this site behavior.
""".strip(),
    "orders_tracking_and_delivery": """
The website includes a strong order tracking flow. Orders are tied to the logged-in user and can be viewed from My Orders or an individual order detail page.
Each order stores status, tracking status, current location, payment information, timestamps for shipment milestones, estimated delivery date, and estimated
delivery time. The My Orders page groups orders into filters like all, active, delivered, and cancelled, and shows progress and status updates for each order.

Tracking statuses include Pending, Paid, Shipped, Out for Delivery, Delivered, and Cancelled. The system also tracks current location defaults such as Warehouse,
Main Transit Hub, Local Delivery Center, or Delivered to your address, depending on status. If a user asks where an order is, whether it has shipped, when it is
arriving, or what the latest order status means, the assistant should answer using these order fields rather than generic shipping language.

Delivery estimation exists at the order level. Estimated delivery dates are generated, and some time-window logic is also present. Bangalore addresses can receive
special time behavior for delivery windows. The assistant should therefore know that delivery guidance is not a random statement; the website has real estimated
delivery fields and user-specific order context. For signed-in users, questions about order delivery should prefer actual latest-order data when available.
""".strip(),
    "cancellations_and_refunds": """
Orders can be cancelled from the My Orders area as long as they are not already delivered or already cancelled. The cancellation flow requires a reason and allows
an additional comment. If the order was paid online, refund handling begins after cancellation. The website has refund statuses such as None, Processing, and Completed.
For paid orders, the code attempts a Razorpay refund through the configured payment client. If a refund succeeds, the refund status becomes Completed; otherwise it can
remain in Processing state.

The assistant should therefore answer cancellation and refund questions very concretely. It should explain that delivered orders cannot be cancelled from the store panel,
that cancellation happens from My Orders, that a reason is required, and that paid orders trigger refund processing. If a user asks whether they can return or cancel, the
assistant should distinguish between cancellation before delivery and post-delivery expectations rather than giving a vague policy statement.

Because this store has an actual order model and cancellation fields, the support assistant should talk in terms of real order flow: pending and active orders may be
cancellable, delivered orders are not cancellable from the current flow, and paid cancellations can initiate refunds. This gives the chatbot grounded answers about what
the website really supports.
""".strip(),
    "wishlist_reviews_and_addresses": """
Wishlist, reviews, and saved addresses are important support topics because they are personal utility features that users ask about often. Wishlist allows logged-in users
to save products for later. Products can be added to wishlist, removed from wishlist, and moved from wishlist to cart. If a user is not logged in, the assistant should
explain that wishlist is available after sign-in and that saved items are tied to the user account.

Reviews are attached to products and linked to both the product and the user. Logged-in users can submit a rating and comment, and updating a previous review is supported
through update-or-create logic. On the product detail page, review count and average rating are visible. So if a customer asks whether they can review a product, where to
review it, or why they need login to review, the assistant should explain the actual review behavior of the site.

Saved Addresses are tied to the user account and managed from My Address. Users can add addresses and set a default address. Checkout depends on the default address for
pre-filling shipping details and determining whether the page is ready for a smooth checkout experience. If someone asks how to update delivery address, save a new address,
or make one address the default, the assistant should route them straight to the Saved Addresses area and explain the default behavior clearly.
""".strip(),
    "support_behavior": """
The support assistant on this website should behave like a store operations guide, not a generic internet chatbot. It should answer directly, stay grounded in the actual
website, and prefer real website facts over decorative language. That means it should know page names, route purposes, user-state differences, product facts, category facts,
payment methods, tracking logic, cancellation logic, review handling, wishlist handling, and address handling. It should also know current database facts like product count,
category count, discounts, stock, and product detail information.

When users ask simple questions, the assistant should respond simply and directly. When users ask site questions, it should answer with route-aware guidance. When users ask
product questions, it should answer with actual product data. When users ask comparative questions like which product has a higher discount, which item is cheaper, which page
they are on, or which product is trending, it should infer the best answer from the site state and database. For example, "trending" on this site can reasonably be inferred
from a combination of reviews, discounts, stock visibility, and premium merchandising prominence because there is no explicit sales ranking field in the current database.

Most importantly, the assistant should avoid useless fallback patterns. If it does not know something exactly, it should say what it can infer from the site and offer the
closest supported answer instead of repeating a generic support introduction. The goal is to make the assistant feel trained on the actual website, not merely attached to it.
""".strip(),
}


# ================= OTP =================
def generate_otp():
    return str(random.randint(100000, 999999))


# ================= HOME =================
def home(request):
    wishlist_product_ids = set()
    if request.user.is_authenticated:
        wishlist_product_ids = set(
            Wishlist.objects.filter(user=request.user).values_list("product_id", flat=True)
        )

    return render(request, "index.html", {
        "products": Product.objects.all(),
        "categories": Category.objects.all(),
        "wishlist_product_ids": wishlist_product_ids,
    })


def _get_admin_report_context():
    revenue_expression = ExpressionWrapper(
        F("price") * F("quantity"),
        output_field=DecimalField(max_digits=12, decimal_places=2),
    )
    current_time = timezone.now()
    last_7_days = current_time - timedelta(days=7)
    last_30_days = current_time - timedelta(days=30)

    orders = Order.objects.select_related("user")
    order_items = OrderItem.objects.select_related("product", "order")
    non_cancelled_items = order_items.exclude(order__status=Order.STATUS_CANCELLED)

    total_orders = orders.count()
    total_revenue = non_cancelled_items.aggregate(total=Sum(revenue_expression))["total"] or Decimal("0.00")
    weekly_revenue = (
        non_cancelled_items.filter(order__created_at__gte=last_7_days).aggregate(total=Sum(revenue_expression))["total"]
        or Decimal("0.00")
    )
    monthly_revenue = (
        non_cancelled_items.filter(order__created_at__gte=last_30_days).aggregate(total=Sum(revenue_expression))["total"]
        or Decimal("0.00")
    )
    average_order_value = (
        total_revenue / total_orders if total_orders else Decimal("0.00")
    )

    status_summary = list(
        orders.values("status").annotate(total=Count("id")).order_by("-total", "status")
    )
    top_products = list(
        non_cancelled_items.values("product__name", "product__stock")
        .annotate(
            units_sold=Sum("quantity"),
            revenue=Sum(revenue_expression),
            orders_count=Count("order", distinct=True),
        )
        .order_by("-units_sold", "-revenue")[:5]
    )
    category_summary = list(
        Category.objects.annotate(
            product_count=Count("product"),
            avg_price=Avg("product__price"),
        ).order_by("-product_count", "name")[:5]
    )
    recent_orders = list(
        orders.order_by("-created_at")[:6]
    )
    recent_reviews = list(
        Review.objects.select_related("product", "user").order_by("-created_at")[:4]
    )

    return {
        "report_generated_at": current_time,
        "total_revenue": total_revenue,
        "weekly_revenue": weekly_revenue,
        "monthly_revenue": monthly_revenue,
        "average_order_value": average_order_value,
        "total_orders": total_orders,
        "active_orders": orders.exclude(
            status__in=[Order.STATUS_DELIVERED, Order.STATUS_CANCELLED]
        ).count(),
        "delivered_orders": orders.filter(status=Order.STATUS_DELIVERED).count(),
        "cancelled_orders": orders.filter(status=Order.STATUS_CANCELLED).count(),
        "total_customers": User.objects.count(),
        "new_customers_30d": User.objects.filter(date_joined__gte=last_30_days).count(),
        "total_products": Product.objects.count(),
        "low_stock_products": Product.objects.filter(stock__lte=5).count(),
        "out_of_stock_products": Product.objects.filter(stock__lte=0).count(),
        "wishlist_saves": Wishlist.objects.count(),
        "review_count": Review.objects.count(),
        "status_summary": status_summary,
        "top_products": top_products,
        "category_summary": category_summary,
        "recent_orders": recent_orders,
        "recent_reviews": recent_reviews,
    }


@staff_member_required
def admin_report(request):
    context = _get_admin_report_context()
    return render(request, "admin/report.html", context)


@csrf_exempt
@staff_member_required
def admin_report_chat(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST is allowed."}, status=405)

    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON payload."}, status=400)

    message = (payload.get("message") or "").strip().lower()
    if not message:
        return JsonResponse({"error": "Message is required."}, status=400)

    context = _get_admin_report_context()
    top_product = context["top_products"][0] if context["top_products"] else None
    top_status = context["status_summary"][0] if context["status_summary"] else None
    top_category = context["category_summary"][0] if context["category_summary"] else None

    if any(term in message for term in ["revenue", "sales", "money", "earnings"]):
        return JsonResponse({
            "reply": (
                f"Total revenue is Rs. {context['total_revenue']:.2f}. "
                f"Revenue in the last 7 days is Rs. {context['weekly_revenue']:.2f}, "
                f"and in the last 30 days it is Rs. {context['monthly_revenue']:.2f}."
            )
        })

    if any(term in message for term in ["order", "orders", "pipeline", "status"]):
        if top_status:
            return JsonResponse({
                "reply": (
                    f"There are {context['total_orders']} total orders. "
                    f"The biggest order bucket right now is {top_status['status']} with {top_status['total']} orders. "
                    f"Delivered orders are {context['delivered_orders']} and cancelled orders are {context['cancelled_orders']}."
                )
            })

    if any(term in message for term in ["product", "top product", "best seller", "best-selling", "inventory", "stock"]):
        if top_product:
            return JsonResponse({
                "reply": (
                    f"The current top product is {top_product['product__name']} with {top_product['units_sold']} units sold "
                    f"across {top_product['orders_count']} orders, generating Rs. {top_product['revenue']:.2f}. "
                    f"There are {context['low_stock_products']} low-stock products and {context['out_of_stock_products']} out-of-stock products."
                )
            })

    if any(term in message for term in ["customer", "customers", "user", "users", "review", "reviews", "feedback"]):
        review_note = (
            f"There are {context['review_count']} reviews recorded."
            if context["review_count"]
            else "There are no customer reviews recorded yet."
        )
        return JsonResponse({
            "reply": (
                f"The store has {context['total_customers']} customers, with {context['new_customers_30d']} new customers in the last 30 days. "
                f"{review_note} Wishlist saves currently total {context['wishlist_saves']}."
            )
        })

    if any(term in message for term in ["category", "categories", "catalog"]):
        if top_category:
            avg_price = ""
            if top_category.avg_price:
                avg_price = f" with an average price of Rs. {top_category.avg_price:.2f}"
            return JsonResponse({
                "reply": (
                    f"The largest category in the current report is {top_category.name} with {top_category.product_count} products{avg_price}. "
                    f"The full catalog currently has {context['total_products']} products."
                )
            })

    return JsonResponse({
        "reply": (
            "I can help summarize revenue, orders, top products, inventory risk, categories, customers, and feedback from this admin report. "
            "Try asking something like 'What is the revenue trend?' or 'Which product is performing best?'"
        )
    })


# ================= SEARCH =================
def search(request):
    query = request.GET.get("q")
    products = Product.objects.filter(name__icontains=query) if query else Product.objects.all()
    wishlist_product_ids = set()

    if request.user.is_authenticated:
        wishlist_product_ids = set(
            Wishlist.objects.filter(user=request.user).values_list("product_id", flat=True)
        )

    return render(request, "index.html", {
        "products": products,
        "categories": Category.objects.all(),
        "query": query,
        "wishlist_product_ids": wishlist_product_ids,
    })


# ================= CATEGORY =================
def category_products(request, id):
    category = get_object_or_404(Category, id=id)
    wishlist_product_ids = set()

    if request.user.is_authenticated:
        wishlist_product_ids = set(
            Wishlist.objects.filter(user=request.user).values_list("product_id", flat=True)
        )

    return render(request, "index.html", {
        "products": Product.objects.filter(category=category),
        "categories": Category.objects.all(),
        "wishlist_product_ids": wishlist_product_ids,
    })


# ================= REGISTER =================
def register(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        if password1 != password2:
            messages.error(request, "Passwords do not match")
            return redirect("register")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists")
            return redirect("register")

        user = User.objects.create_user(username=username, email=email, password=password1)
        login(request, user)

        return redirect("home")

    return render(request, "register.html")


# ================= LOGIN OTP =================
def send_otp(request):
    if request.method == "POST":
        email = request.POST.get("login")

        user = User.objects.filter(email=email).first()
        if not user:
            user = User.objects.create_user(username=email.split("@")[0], email=email)

        otp = generate_otp()
        OTP.objects.create(user=user, otp=otp)

        send_mail("Your OTP", f"OTP: {otp}", settings.EMAIL_HOST_USER, [email])

        request.session["otp_user"] = user.id
        return redirect("verify_otp")

    return render(request, "login.html")


def verify_otp(request):
    if request.method == "POST":
        otp_input = request.POST.get("otp")
        user_id = request.session.get("otp_user")

        otp = OTP.objects.filter(user_id=user_id).last()

        if otp and otp.otp == otp_input:
            user = User.objects.get(id=user_id)
            login(request, user)
            return redirect("home")

        messages.error(request, "Invalid OTP")

    return render(request, "verify_otp.html")


def logout_view(request):
    logout(request)
    return redirect("home")


# ================= PRODUCT =================
def product_detail(request, id):
    product = get_object_or_404(Product, id=id)
    reviews = product.reviews.select_related("user").order_by("-created_at")
    review_count = reviews.count()
    avg_rating = round(sum(review.rating for review in reviews) / review_count, 1) if review_count else 0
    saving = product.price - product.discounted_price()
    user_review = None

    if request.user.is_authenticated:
        user_review = reviews.filter(user=request.user).first()

    return render(request, "product_detail.html", {
        "product": product,
        "reviews": reviews,
        "review_count": review_count,
        "avg_rating": avg_rating,
        "saving": saving,
        "user_review": user_review,
    })


# ================= REVIEW =================
@login_required
def add_review(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    Review.objects.update_or_create(
        product=product,
        user=request.user,
        defaults={
            "rating": request.POST.get("rating"),
            "comment": request.POST.get("comment")
        }
    )

    return redirect("product_detail", id=product.id)


# ================= CART =================
def cart(request):
    cart = request.session.get("cart", {})
    products = []
    total = Decimal("0.00")

    for pid, qty in cart.items():
        product = Product.objects.get(id=pid)

        price = product.discounted_price()
        total_price = price * qty

        product.quantity = qty
        product.final_price = price
        product.total_price = total_price

        total += total_price
        products.append(product)

    return render(request, "cart.html", {
        "products": products,
        "total": total
    })


def add_to_cart(request, product_id):
    cart = request.session.get("cart", {})
    cart[str(product_id)] = cart.get(str(product_id), 0) + 1

    request.session["cart"] = cart
    request.session.modified = True

    return redirect("cart")


def increase_cart(request, product_id):
    cart = request.session.get("cart", {})
    cart[str(product_id)] += 1

    request.session["cart"] = cart
    request.session.modified = True

    return redirect("cart")


def decrease_cart(request, product_id):
    cart = request.session.get("cart", {})

    if cart[str(product_id)] > 1:
        cart[str(product_id)] -= 1
    else:
        del cart[str(product_id)]

    request.session["cart"] = cart
    request.session.modified = True

    return redirect("cart")


def remove_from_cart(request, product_id):
    cart = request.session.get("cart", {})
    cart.pop(str(product_id), None)

    request.session["cart"] = cart
    request.session.modified = True

    return redirect("cart")


def _get_cart_products_and_total(cart):
    cart_products = []
    total = Decimal("0.00")

    for pid, qty in cart.items():
        product = Product.objects.get(id=int(pid))
        quantity = int(qty)
        price = product.discounted_price()
        total += price * quantity
        cart_products.append({
            "product": product,
            "quantity": quantity,
            "price": price,
        })

    return cart_products, total


def _create_order_items(order, cart_products):
    for entry in cart_products:
        OrderItem.objects.create(
            order=order,
            product=entry["product"],
            quantity=entry["quantity"],
            price=entry["price"],
        )


def _get_estimated_delivery_date():
    return timezone.localdate() + timedelta(days=5)


def _get_estimated_delivery_time(city):
    if city and city.strip().lower() == "bangalore":
        return "before 4:00 PM"

    time_slots = [
        "before 12:00 PM",
        "before 2:00 PM",
        "before 4:00 PM",
        "before 6:00 PM",
        "before 9:00 PM",
    ]
    return random.choice(time_slots)


def _get_default_address(user):
    return Address.objects.filter(user=user, is_default=True).first()


def _set_default_address(address):
    Address.objects.filter(user=address.user).update(is_default=False)
    address.is_default = True
    address.save(update_fields=["is_default"])


def _refund_paid_order(order):
    if not order.razorpay_payment_id:
        return

    client = razorpay.Client(auth=(
        settings.RAZORPAY_KEY_ID,
        settings.RAZORPAY_KEY_SECRET
    ))
    refund_amount = int(order.total_amount * Decimal("100"))
    client.payment.refund(order.razorpay_payment_id, {"amount": refund_amount})


# ================= CHECKOUT =================
@login_required
def checkout(request):

    cart = request.session.get("cart", {})
    default_address = _get_default_address(request.user)

    if request.method == "POST":
        if request.POST.get("payment_method") == "cod":
            cart_products, total = _get_cart_products_and_total(cart)
            full_name = default_address.full_name if default_address else "COD User"
            address_text = default_address.address if default_address else "N/A"
            city = default_address.city if default_address else "N/A"
            pincode = default_address.pincode if default_address else "000000"

            order = Order.objects.create(
                user=request.user,
                full_name=full_name,
                address=address_text,
                city=city,
                pincode=pincode,
                total_amount=total,
                payment_method=Order.PAYMENT_METHOD_COD,
                status=Order.STATUS_PENDING,
                estimated_delivery=_get_estimated_delivery_date(),
                estimated_delivery_time=_get_estimated_delivery_time(city),
            )
            _create_order_items(order, cart_products)

            # clear cart
            request.session["cart"] = {}
            request.session.modified = True

            return redirect("my_orders")

    _, total = _get_cart_products_and_total(cart)

    return render(request, "checkout.html", {
        "total": total,
        "razorpay_key": settings.RAZORPAY_KEY_ID,
        "default_address": default_address,
        "has_default_address": bool(default_address),
    })


# ================= CREATE PAYMENT (FAST) =================
@login_required
def create_payment(request):

    cart = request.session.get("cart", {})
    cart_products, total = _get_cart_products_and_total(cart)
    default_address = _get_default_address(request.user)
    full_name = default_address.full_name if default_address else "Online Payment User"
    address_text = default_address.address if default_address else "N/A"
    city = default_address.city if default_address else "N/A"
    pincode = default_address.pincode if default_address else "000000"

    # Convert to paise
    amount = int(total * Decimal("100"))

    client = razorpay.Client(auth=(
        settings.RAZORPAY_KEY_ID,
        settings.RAZORPAY_KEY_SECRET
    ))

    order = client.order.create({
        "amount": amount,
        "currency": "INR",
        "payment_capture": 1
    })

    db_order = Order.objects.create(
        user=request.user,
        full_name=full_name,
        address=address_text,
        city=city,
        pincode=pincode,
        total_amount=total,
        payment_method=Order.PAYMENT_METHOD_ONLINE,
        status=Order.STATUS_PENDING,
        estimated_delivery=_get_estimated_delivery_date(),
        estimated_delivery_time=_get_estimated_delivery_time(city),
        razorpay_order_id=order["id"],
    )
    _create_order_items(db_order, cart_products)

    return JsonResponse(order)


# ================= VERIFY PAYMENT =================
@csrf_exempt
def verify_payment(request):

    data = json.loads(request.body)

    client = razorpay.Client(auth=(
        settings.RAZORPAY_KEY_ID,
        settings.RAZORPAY_KEY_SECRET
    ))

    try:
        client.utility.verify_payment_signature({
            "razorpay_order_id": data["razorpay_order_id"],
            "razorpay_payment_id": data["razorpay_payment_id"],
            "razorpay_signature": data["razorpay_signature"]
        })

        order = Order.objects.filter(
            razorpay_order_id=data["razorpay_order_id"],
            user=request.user,
        ).order_by("-id").first()

        if order:
            order.status = Order.STATUS_PAID
            order.is_paid = True
            order.razorpay_payment_id = data["razorpay_payment_id"]
            order.razorpay_signature = data["razorpay_signature"]
            order.save(update_fields=[
                "status",
                "is_paid",
                "razorpay_payment_id",
                "razorpay_signature",
            ])
            request.session["cart"] = {}
            request.session.modified = True

        return JsonResponse({"status": "success"})

    except Exception:
        return JsonResponse({"status": "failed"})


# ================= ORDERS =================
@login_required
@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    for item in order.items.all():
        item.total = item.price * item.quantity

    return render(request, "order_detail.html", {"order": order})


@login_required
def my_orders(request):
    badge_classes = {
        Order.TRACKING_STATUS_PENDING: "status-pending",
        Order.TRACKING_STATUS_PAID: "status-paid",
        Order.TRACKING_STATUS_SHIPPED: "status-shipped",
        Order.TRACKING_STATUS_OUT_FOR_DELIVERY: "status-out-for-delivery",
        Order.TRACKING_STATUS_DELIVERED: "status-delivered",
        Order.TRACKING_STATUS_CANCELLED: "status-cancelled",
    }
    progress_values = {
        Order.TRACKING_STATUS_PENDING: 25,
        Order.TRACKING_STATUS_PAID: 50,
        Order.TRACKING_STATUS_SHIPPED: 75,
        Order.TRACKING_STATUS_OUT_FOR_DELIVERY: 90,
        Order.TRACKING_STATUS_DELIVERED: 100,
        Order.TRACKING_STATUS_CANCELLED: 0,
    }
    tracking_messages = {
        Order.TRACKING_STATUS_PENDING: "Your order is being prepared.",
        Order.TRACKING_STATUS_PAID: "Payment confirmed. Preparing shipment.",
        Order.TRACKING_STATUS_SHIPPED: "Your order is shipped and will arrive soon.",
        Order.TRACKING_STATUS_OUT_FOR_DELIVERY: "Out for delivery today.",
        Order.TRACKING_STATUS_DELIVERED: "Delivered successfully.",
        Order.TRACKING_STATUS_CANCELLED: "This order has been cancelled.",
    }

    all_orders = Order.objects.filter(user=request.user).prefetch_related("items__product").order_by("-created_at")
    total_orders = all_orders.count()
    delivered_orders = all_orders.filter(status=Order.STATUS_DELIVERED).count()
    cancelled_orders = all_orders.filter(status=Order.STATUS_CANCELLED).count()
    active_orders = all_orders.exclude(status__in=[Order.STATUS_DELIVERED, Order.STATUS_CANCELLED]).count()

    print("Delivered:", delivered_orders)
    print("Cancelled:", cancelled_orders)
    print("Active:", active_orders)

    current_filter = request.GET.get("filter", "all")
    orders = all_orders

    if current_filter == "active":
        orders = all_orders.exclude(status__in=[Order.STATUS_DELIVERED, Order.STATUS_CANCELLED])
    elif current_filter == "delivered":
        orders = all_orders.filter(status=Order.STATUS_DELIVERED)
    elif current_filter == "cancelled":
        orders = all_orders.filter(status=Order.STATUS_CANCELLED)
    else:
        current_filter = "all"

    enable_auto_refresh = False

    def format_tracking_time(value):
        if not value:
            return "Waiting for update"
        return timezone.localtime(value).strftime("%b %d, %Y - %I:%M %p")

    for order in orders:
        order.badge_class = badge_classes.get(order.tracking_status, "status-pending")
        order.progress_value = progress_values.get(order.tracking_status, 25)
        order.tracking_message = tracking_messages.get(order.tracking_status, "Your order is being prepared.")
        order.can_cancel = order.status != Order.STATUS_DELIVERED and order.status != Order.STATUS_CANCELLED
        payment_confirmed = order.is_paid or order.status == Order.STATUS_PAID or bool(order.razorpay_payment_id)
        payment_confirmed_at = None

        if payment_confirmed:
            payment_confirmed_at = (
                order.shipped_at
                or order.out_for_delivery_at
                or order.delivered_at
                or order.ordered_at
                or order.created_at
            )

        if order.tracking_status not in [Order.TRACKING_STATUS_DELIVERED, Order.TRACKING_STATUS_CANCELLED]:
            enable_auto_refresh = True

        delivery_time = order.estimated_delivery_time or _get_estimated_delivery_time(order.city)

        if order.tracking_status == Order.TRACKING_STATUS_DELIVERED and order.delivered_at:
            order.delivery_display = f"Delivered on {format_tracking_time(order.delivered_at)}"
        elif order.estimated_delivery:
            order.delivery_display = (
                f"Expected by {order.estimated_delivery.strftime('%b %d, %Y')} {delivery_time}"
            )
        else:
            order.delivery_display = "Delivery estimate will be updated soon"

        if order.tracking_status == Order.TRACKING_STATUS_PENDING and order.estimated_delivery:
            order.tracking_message = (
                f"Your order is being prepared and is expected by "
                f"{order.estimated_delivery.strftime('%b %d, %Y')} {delivery_time}."
            )

        if order.tracking_status == Order.TRACKING_STATUS_PAID and order.estimated_delivery:
            order.tracking_message = (
                f"Payment confirmed. Your order is being packed and is expected by "
                f"{order.estimated_delivery.strftime('%b %d, %Y')} {delivery_time}."
            )

        if order.tracking_status == Order.TRACKING_STATUS_SHIPPED and order.estimated_delivery:
            order.tracking_message = (
                f"Your order is shipped and will arrive "
                f"{order.estimated_delivery.strftime('%b %d, %Y')} {delivery_time}."
            )

        if order.tracking_status == Order.TRACKING_STATUS_OUT_FOR_DELIVERY and order.estimated_delivery:
            order.tracking_message = f"Out for delivery, arriving today {delivery_time}."

        order.timeline_steps = [
            {
                "label": "Order Placed",
                "completed": True,
                "timestamp": format_tracking_time(order.ordered_at or order.created_at),
            },
            {
                "label": "Payment Confirmed",
                "completed": payment_confirmed,
                "timestamp": format_tracking_time(payment_confirmed_at) if payment_confirmed else "Waiting for payment",
            },
            {
                "label": "Shipped",
                "completed": bool(order.shipped_at),
                "timestamp": format_tracking_time(order.shipped_at) if order.shipped_at else "Waiting for shipment",
            },
            {
                "label": "Out for Delivery",
                "completed": bool(order.out_for_delivery_at),
                "timestamp": format_tracking_time(order.out_for_delivery_at) if order.out_for_delivery_at else "Not out for delivery yet",
            },
            {
                "label": "Delivered",
                "completed": bool(order.delivered_at),
                "timestamp": format_tracking_time(order.delivered_at) if order.delivered_at else "Not delivered yet",
            },
        ]

    return render(request, "my_orders.html", {
        "orders": orders,
        "has_orders": total_orders > 0,
        "current_filter": current_filter,
        "enable_auto_refresh": enable_auto_refresh,
        "total_orders": total_orders,
        "delivered_orders": delivered_orders,
        "active_orders": active_orders,
        "cancelled_orders": cancelled_orders,
    })


@login_required
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if request.method != "POST":
        return redirect("my_orders")

    if order.status == Order.STATUS_DELIVERED or order.status == Order.STATUS_CANCELLED:
        messages.error(request, "This order cannot be cancelled.")
        return redirect("my_orders")

    reason = request.POST.get("reason", "").strip()
    comment = request.POST.get("comment", "").strip()

    if not reason:
        messages.error(request, "Please select a cancellation reason.")
        return redirect("my_orders")

    was_paid = order.is_paid or order.status == Order.STATUS_PAID
    order.status = Order.STATUS_CANCELLED
    order.cancel_reason = reason
    order.cancel_comment = comment
    order.cancelled_at = timezone.now()
    order.refund_status = Order.REFUND_NONE

    if was_paid:
        order.refund_status = Order.REFUND_PROCESSING

        try:
            _refund_paid_order(order)
            order.refund_status = Order.REFUND_COMPLETED
        except Exception:
            order.refund_status = Order.REFUND_PROCESSING

    order.save(update_fields=[
        "status",
        "cancel_reason",
        "cancel_comment",
        "cancelled_at",
        "refund_status",
    ])
    messages.success(request, "Your order has been cancelled.")
    return redirect("my_orders")


# ================= PROFILE =================
@login_required
def profile(request):
    default_address = _get_default_address(request.user)
    phone = default_address.phone if default_address else ""
    order_count = Order.objects.filter(user=request.user).count()
    delivered_count = Order.objects.filter(user=request.user, status=Order.STATUS_DELIVERED).count()
    address_count = Address.objects.filter(user=request.user).count()
    wishlist_total = Wishlist.objects.filter(user=request.user).count()
    recent_order = Order.objects.filter(user=request.user).order_by("-created_at").first()

    if request.method == "POST":
        request.user.username = request.POST.get("name", request.user.username).strip() or request.user.username
        request.user.email = request.POST.get("email", request.user.email).strip()
        request.user.save(update_fields=["username", "email"])
        messages.success(request, "Profile updated successfully.")
        return redirect("profile")

    return render(request, "profile.html", {
        "phone": phone,
        "default_address": default_address,
        "order_count": order_count,
        "delivered_count": delivered_count,
        "address_count": address_count,
        "wishlist_total": wishlist_total,
        "recent_order": recent_order,
    })


# ================= ADDRESS =================
@login_required
def my_address(request):
    if request.method == "POST":
        action = request.POST.get("action")

        if action == "add":
            address = Address.objects.create(
                user=request.user,
                full_name=request.POST.get("full_name", "").strip(),
                phone=request.POST.get("phone", "").strip(),
                address=request.POST.get("address", "").strip(),
                city=request.POST.get("city", "").strip(),
                pincode=request.POST.get("pincode", "").strip(),
                is_default=request.POST.get("is_default") == "on",
            )

            if address.is_default or not Address.objects.filter(user=request.user, is_default=True).exclude(id=address.id).exists():
                _set_default_address(address)

            messages.success(request, "Address saved successfully.")
            return redirect("my_address")

        if action == "set_default":
            address = get_object_or_404(Address, id=request.POST.get("address_id"), user=request.user)
            _set_default_address(address)
            messages.success(request, "Default address updated.")
            return redirect("my_address")

    addresses = Address.objects.filter(user=request.user).order_by("-is_default", "-id")
    default_address = addresses.filter(is_default=True).first()

    return render(request, "address.html", {
        "addresses": addresses,
        "default_address": default_address,
    })


# ================= WISHLIST =================
@login_required
def wishlist(request):
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related("product").order_by("-created_at")
    in_stock_count = sum(1 for item in wishlist_items if item.product.stock > 0)

    return render(request, "wishlist.html", {
        "wishlist_items": wishlist_items,
        "in_stock_count": in_stock_count,
    })


@login_required
def add_to_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    Wishlist.objects.get_or_create(user=request.user, product=product)
    return redirect(request.GET.get("next", "wishlist"))


@login_required
def remove_from_wishlist(request, product_id):
    Wishlist.objects.filter(user=request.user, product_id=product_id).delete()
    return redirect(request.GET.get("next", "wishlist"))


@login_required
def move_wishlist_to_cart(request, product_id):
    get_object_or_404(Product, id=product_id)

    cart = request.session.get("cart", {})
    cart[str(product_id)] = cart.get(str(product_id), 0) + 1
    request.session["cart"] = cart
    request.session.modified = True

    Wishlist.objects.filter(user=request.user, product_id=product_id).delete()
    return redirect("wishlist")


def _format_currency(value):
    return f"₹{value}"


def _format_product_brief(product):
    return {
        "id": product.id,
        "name": product.name,
        "price": _format_currency(product.discounted_price()),
        "url": f"/product/{product.id}/",
        "category": product.category.name if product.category else "Herbal care",
        "discount_percent": product.discount_percent,
        "stock": product.stock,
    }


def _normalize_message(message):
    cleaned = message.lower()
    for ch in [",", ".", "?", "!", ":", ";", "(", ")", "/", "\\", "-", "_"]:
        cleaned = cleaned.replace(ch, " ")
    return " ".join(cleaned.split())


def _contains_any(text, phrases):
    return any(phrase in text for phrase in phrases)


def _score_product_match(product, text, words):
    score = 0
    name = product.name.lower()
    category = product.category.name.lower() if product.category else ""
    description = product.description.lower()

    if name in text:
        score += 12

    for word in words:
        if word in name:
            score += 4
        if category and word in category:
            score += 3
        if word in description:
            score += 1

    return score


def _get_best_chat_product_matches(message, limit=3):
    text = _normalize_message(message)
    words = [word for word in text.split() if len(word) >= 3]
    products = Product.objects.select_related("category").all()
    ranked = []

    for product in products:
        score = _score_product_match(product, text, words)
        if score > 0:
            ranked.append((score, product))

    ranked.sort(key=lambda item: (-item[0], item[1].name.lower()))
    return [product for _, product in ranked[:limit]]


def _get_chat_product_matches(message, limit=3):
    ranked_matches = _get_best_chat_product_matches(message, limit=limit)
    if ranked_matches:
        return ranked_matches

    words = [word.strip() for word in message.split() if len(word.strip()) >= 3]
    query = Q()

    for word in words[:6]:
        query |= Q(name__icontains=word) | Q(description__icontains=word)

    if not query:
        return Product.objects.none()

    return list(Product.objects.filter(query).select_related("category").distinct()[:limit])


def _get_direct_product_answer(product, text):
    discounted_price = product.discounted_price()
    category_name = product.category.name if product.category else "Herbal care"

    if _contains_any(text, ["price", "cost", "amount", "rate", "how much"]):
        if product.discount_percent > 0:
            return {
                "reply": (
                    f"{product.name} is currently available for {_format_currency(discounted_price)}. "
                    f"The original price is {_format_currency(product.price)}, so you save {product.discount_percent}%."
                ),
                "products": [_format_product_brief(product)],
                "quick_actions": [
                    {"label": "Open product", "url": f"/product/{product.id}/"},
                    {"label": "Add to cart", "url": f"/add-to-cart/{product.id}/"},
                ],
            }
        return {
            "reply": f"{product.name} is currently priced at {_format_currency(discounted_price)}.",
            "products": [_format_product_brief(product)],
            "quick_actions": [
                {"label": "Open product", "url": f"/product/{product.id}/"},
                {"label": "Add to cart", "url": f"/add-to-cart/{product.id}/"},
            ],
        }

    if _contains_any(text, ["stock", "available", "availability", "in stock", "out of stock"]):
        if product.stock > 0:
            return {
                "reply": f"Yes, {product.name} is available right now with {product.stock} unit{'s' if product.stock != 1 else ''} in stock.",
                "products": [_format_product_brief(product)],
                "quick_actions": [
                    {"label": "View product", "url": f"/product/{product.id}/"},
                    {"label": "Add to cart", "url": f"/add-to-cart/{product.id}/"},
                ],
            }
        return {
            "reply": f"{product.name} is currently out of stock.",
            "products": [_format_product_brief(product)],
            "quick_actions": [
                {"label": "Browse alternatives", "url": f"/search/?q={category_name}"},
            ],
        }

    if _contains_any(text, ["benefit", "benefits", "use", "used for", "good for", "why", "about", "details", "description"]):
        return {
            "reply": f"{product.name} is in {category_name}. {product.description[:260]}",
            "products": [_format_product_brief(product)],
            "quick_actions": [
                {"label": "Read full details", "url": f"/product/{product.id}/"},
                {"label": "Similar products", "url": f"/search/?q={category_name}"},
            ],
        }

    if _contains_any(text, ["discount", "offer", "sale"]):
        if product.discount_percent > 0:
            return {
                "reply": f"Yes, {product.name} currently has a {product.discount_percent}% discount. The current price is {_format_currency(discounted_price)}.",
                "products": [_format_product_brief(product)],
                "quick_actions": [
                    {"label": "Open product", "url": f"/product/{product.id}/"},
                ],
            }
        return {
            "reply": f"{product.name} does not have an active discount right now. The current price is {_format_currency(discounted_price)}.",
            "products": [_format_product_brief(product)],
            "quick_actions": [
                {"label": "Open product", "url": f"/product/{product.id}/"},
            ],
        }

    return {
        "reply": (
            f"The closest match to your question is {product.name}. "
            f"It belongs to {category_name} and is currently priced at {_format_currency(discounted_price)}."
        ),
        "products": [_format_product_brief(product)],
        "quick_actions": [
            {"label": "Open product", "url": f"/product/{product.id}/"},
            {"label": "Add to cart", "url": f"/add-to-cart/{product.id}/"},
        ],
    }


def _get_current_page_product(current_path):
    if not current_path:
        return None

    path = current_path.strip("/")
    parts = path.split("/")
    if len(parts) == 2 and parts[0] == "product" and parts[1].isdigit():
        return Product.objects.select_related("category").filter(id=int(parts[1])).first()
    return None


def _get_site_stats():
    total_products = Product.objects.count()
    total_categories = Category.objects.count()
    in_stock_products = Product.objects.filter(stock__gt=0).count()
    discounted_products = Product.objects.filter(discount_percent__gt=0).count()
    return {
        "total_products": total_products,
        "total_categories": total_categories,
        "in_stock_products": in_stock_products,
        "discounted_products": discounted_products,
    }


def _get_top_discounted_products(limit=3):
    return list(
        Product.objects.select_related("category")
        .filter(discount_percent__gt=0)
        .order_by("-discount_percent", "price", "name")[:limit]
    )


def _get_cheapest_products(limit=3):
    products = list(Product.objects.select_related("category").all())
    products.sort(key=lambda product: (product.discounted_price(), product.name.lower()))
    return products[:limit]


def _get_most_expensive_products(limit=3):
    products = list(Product.objects.select_related("category").all())
    products.sort(key=lambda product: (-product.discounted_price(), product.name.lower()))
    return products[:limit]


def _build_product_comparison_answer(products, metric):
    if len(products) < 2:
        return None

    if metric == "discount":
        ranked = sorted(products, key=lambda item: (-item.discount_percent, item.name.lower()))
        lead = ranked[0]
        runner = ranked[1]
        return {
            "reply": (
                f"{lead.name} has the higher discount at {lead.discount_percent}% off. "
                f"{runner.name} follows with {runner.discount_percent}% off."
            ),
            "products": [_format_product_brief(product) for product in ranked[:3]],
            "quick_actions": [
                {"label": f"Open {lead.name}", "url": f"/product/{lead.id}/"},
            ],
        }

    if metric == "price":
        ranked = sorted(products, key=lambda item: (item.discounted_price(), item.name.lower()))
        cheaper = ranked[0]
        pricier = ranked[1]
        return {
            "reply": (
                f"{cheaper.name} is cheaper at {_format_currency(cheaper.discounted_price())}. "
                f"{pricier.name} is {_format_currency(pricier.discounted_price())}."
            ),
            "products": [_format_product_brief(product) for product in ranked[:3]],
            "quick_actions": [
                {"label": f"Open {cheaper.name}", "url": f"/product/{cheaper.id}/"},
            ],
        }

    if metric == "stock":
        ranked = sorted(products, key=lambda item: (-item.stock, item.name.lower()))
        lead = ranked[0]
        runner = ranked[1]
        return {
            "reply": (
                f"{lead.name} has more stock right now with {lead.stock} units. "
                f"{runner.name} currently has {runner.stock} units."
            ),
            "products": [_format_product_brief(product) for product in ranked[:3]],
            "quick_actions": [
                {"label": f"Open {lead.name}", "url": f"/product/{lead.id}/"},
            ],
        }

    return None


def _build_page_product_answer(product):
    discounted_price = product.discounted_price()
    review_count = product.reviews.count()
    return {
        "reply": (
            f"You are currently viewing {product.name}. It belongs to "
            f"{product.category.name if product.category else 'Herbal care'}, costs {_format_currency(discounted_price)}, "
            f"has {product.stock} units in stock, and currently has {review_count} customer review{'s' if review_count != 1 else ''}."
        ),
        "products": [_format_product_brief(product)],
        "quick_actions": [
            {"label": "Open product", "url": f"/product/{product.id}/"},
            {"label": "Add to cart", "url": f"/add-to-cart/{product.id}/"},
        ],
    }


def _get_trending_products(limit=3):
    products = list(Product.objects.select_related("category").all())
    scored = []

    for product in products:
        review_count = product.reviews.count()
        score = (
            review_count * 10
            + product.discount_percent * 2
            + min(product.stock, 50) * 0.2
        )
        scored.append((score, product))

    scored.sort(key=lambda item: (-item[0], item[1].name.lower()))
    return [product for _, product in scored[:limit]]


def _get_site_knowledge_answer(text, site_stats, categories):
    knowledge_intents = [
        (
            ["about this website", "about this store", "tell me about this website", "tell me about this store", "website overview", "store overview"],
            "store_overview",
            "Here is a full overview of how this website works."
        ),
        (
            ["catalog", "products page", "product details", "how products work", "about product page"],
            "catalog_and_products",
            "Here is how the catalog and product experience works on this website."
        ),
        (
            ["navigation", "pages", "routes", "where can i", "which pages", "how to browse"],
            "categories_and_navigation",
            "Here is how navigation and major pages work on this website."
        ),
        (
            ["login", "otp", "register", "account", "profile"],
            "account_and_auth",
            "Here is how account and authentication work on this website."
        ),
        (
            ["cart", "checkout", "payment", "cod", "razorpay"],
            "cart_and_checkout",
            "Here is how cart, checkout, and payment work on this website."
        ),
        (
            ["order tracking", "tracking", "delivery", "shipping", "my orders", "order status"],
            "orders_tracking_and_delivery",
            "Here is how orders, tracking, and delivery work on this website."
        ),
        (
            ["cancel", "refund", "return", "cancellation"],
            "cancellations_and_refunds",
            "Here is how cancellation and refund behavior works on this website."
        ),
        (
            ["wishlist", "review", "reviews", "address", "saved address"],
            "wishlist_reviews_and_addresses",
            "Here is how wishlist, reviews, and saved addresses work on this website."
        ),
    ]

    for phrases, section_key, intro in knowledge_intents:
        if _contains_any(text, phrases):
            return {
                "reply": (
                    f"{intro} "
                    f"{SITE_KNOWLEDGE_SECTIONS[section_key]}"
                ),
                "quick_actions": [
                    {"label": "Browse catalog", "url": "/"},
                    {"label": "My orders", "url": "/my-orders/"},
                    {"label": "Saved addresses", "url": "/my-address/"},
                ],
            }

    if _contains_any(text, ["everything about this website", "know everything", "full details of website", "complete website info"]):
        return {
            "reply": (
                f"The website currently has {site_stats['total_products']} products and {site_stats['total_categories']} categories. "
                f"Main categories include {', '.join(categories[:6])}. "
                f"{SITE_KNOWLEDGE_SECTIONS['store_overview']} "
                f"{SITE_KNOWLEDGE_SECTIONS['categories_and_navigation']} "
                f"{SITE_KNOWLEDGE_SECTIONS['cart_and_checkout']}"
            ),
            "quick_actions": [
                {"label": "Store overview", "text": "tell me about this website"},
                {"label": "How checkout works", "text": "how checkout works"},
                {"label": "How order tracking works", "text": "how order tracking works"},
            ],
        }

    return None


def _build_chat_response(request, message):
    text = _normalize_message(message)
    current_path = request.headers.get("X-Current-Path") or request.GET.get("current_path", "")
    current_page_product = _get_current_page_product(current_path)
    site_stats = _get_site_stats()
    cart = request.session.get("cart", {})
    cart_count_total = sum(int(qty) for qty in cart.values())
    categories = list(Category.objects.order_by("name").values_list("name", flat=True)[:8])
    matched_products = list(_get_chat_product_matches(text))
    category_match = Category.objects.filter(name__icontains=text).order_by("name").first()

    quick_actions = [
        {"label": "Shop all", "url": "/"},
        {"label": "Track orders", "url": "/my-orders/"},
        {"label": "Open cart", "url": "/cart/"},
    ]

    if _contains_any(text, ["how many products", "total products", "number of products", "products does this website have"]):
        return {
            "reply": (
                f"This website currently has {site_stats['total_products']} products across "
                f"{site_stats['total_categories']} categories. {site_stats['in_stock_products']} products are in stock right now."
            ),
            "quick_actions": [
                {"label": "Browse catalog", "url": "/"},
                {"label": "Categories", "text": "show all categories"},
            ],
        }

    if _contains_any(text, ["which product is trending", "trending product", "most trending product", "what is trending", "which is in trending"]):
        trending_products = _get_trending_products()
        if trending_products:
            lead = trending_products[0]
            return {
                "reply": (
                    f"The current trending product on this website is {lead.name}. "
                    f"I am inferring trending from visibility signals on the site like review activity, discount strength, and stock presence because the database does not store a direct sales ranking field."
                ),
                "products": [_format_product_brief(product) for product in trending_products],
                "quick_actions": [
                    {"label": f"Open {lead.name}", "url": f"/product/{lead.id}/"},
                    {"label": "Show top discounts", "text": "which product has the highest discount"},
                ],
            }

    if _contains_any(text, ["how many categories", "total categories", "number of categories"]):
        return {
            "reply": (
                f"The store currently has {site_stats['total_categories']} categories, including "
                + ", ".join(categories[:5]) + "."
            ),
            "quick_actions": [{"label": name, "url": f"/search/?q={name}"} for name in categories[:3]],
        }

    if _contains_any(text, ["this page", "this product", "which product is this", "what product is this", "tell me about this page"]) and current_page_product:
        return _build_page_product_answer(current_page_product)

    if _contains_any(text, ["highest discount", "biggest discount", "maximum discount", "higher discount", "best discount"]):
        top_discounted = _get_top_discounted_products()
        if top_discounted:
            lead = top_discounted[0]
            return {
                "reply": (
                    f"The highest discount in the store right now is on {lead.name} at {lead.discount_percent}% off. "
                    f"I’ve also listed a few other discounted products below."
                ),
                "products": [_format_product_brief(product) for product in top_discounted],
                "quick_actions": [
                    {"label": "Open top discount", "url": f"/product/{lead.id}/"},
                    {"label": "Browse deals", "url": "/"},
                ],
            }

    if _contains_any(text, ["cheapest product", "lowest price", "most affordable", "cheap product"]):
        cheapest_products = _get_cheapest_products()
        if cheapest_products:
            lead = cheapest_products[0]
            return {
                "reply": f"The cheapest product right now is {lead.name} at {_format_currency(lead.discounted_price())}.",
                "products": [_format_product_brief(product) for product in cheapest_products],
                "quick_actions": [
                    {"label": "Open cheapest product", "url": f"/product/{lead.id}/"},
                ],
            }

    if _contains_any(text, ["most expensive", "highest price", "costliest product", "premium product"]):
        expensive_products = _get_most_expensive_products()
        if expensive_products:
            lead = expensive_products[0]
            return {
                "reply": f"The most expensive product right now is {lead.name} at {_format_currency(lead.discounted_price())}.",
                "products": [_format_product_brief(product) for product in expensive_products],
                "quick_actions": [
                    {"label": "Open premium product", "url": f"/product/{lead.id}/"},
                ],
            }

    if _contains_any(text, ["show all categories", "list categories", "what categories", "which categories"]):
        return {
            "reply": "The store categories currently include " + ", ".join(categories) + ".",
            "quick_actions": [{"label": name, "url": f"/search/?q={name}"} for name in categories[:4]],
        }

    site_knowledge_answer = _get_site_knowledge_answer(text, site_stats, categories)
    if site_knowledge_answer:
        return site_knowledge_answer

    if len(matched_products) >= 2 and _contains_any(text, ["compare", "higher discount", "more discount", "which is cheaper", "lower price", "more stock"]):
        if _contains_any(text, ["discount", "offer"]):
            comparison = _build_product_comparison_answer(matched_products, "discount")
            if comparison:
                return comparison
        if _contains_any(text, ["cheap", "cheaper", "price", "cost"]):
            comparison = _build_product_comparison_answer(matched_products, "price")
            if comparison:
                return comparison
        if _contains_any(text, ["stock", "available"]):
            comparison = _build_product_comparison_answer(matched_products, "stock")
            if comparison:
                return comparison

    if matched_products:
        lead = matched_products[0]
        product_specific_terms = [
            "price", "cost", "amount", "rate", "how much", "stock", "available", "availability",
            "benefit", "benefits", "use", "used for", "good for", "about", "details", "description",
            "discount", "offer", "sale"
        ]
        exact_name_hit = lead.name.lower() in text
        if exact_name_hit or _contains_any(text, product_specific_terms):
            return _get_direct_product_answer(lead, text)
    elif current_page_product and _contains_any(
        text,
        [
            "price", "cost", "amount", "rate", "how much", "stock", "available", "availability",
            "benefit", "benefits", "use", "used for", "good for", "about", "details", "description",
            "discount", "offer", "sale", "review", "reviews"
        ]
    ):
        if _contains_any(text, ["review", "reviews", "rating"]):
            review_count = current_page_product.reviews.count()
            average_rating = 0
            if review_count:
                average_rating = round(
                    sum(review.rating for review in current_page_product.reviews.all()) / review_count,
                    1,
                )
            return {
                "reply": (
                    f"{current_page_product.name} currently has {review_count} customer review{'s' if review_count != 1 else ''}"
                    + (f" with an average rating of {average_rating}/5." if review_count else ".")
                ),
                "products": [_format_product_brief(current_page_product)],
                "quick_actions": [
                    {"label": "View product", "url": f"/product/{current_page_product.id}/"},
                ],
            }
        return _get_direct_product_answer(current_page_product, text)

    if any(greet in text for greet in ["hello", "hi", "hey", "good morning", "good evening"]):
        return {
            "reply": (
                "Hello! I can help you find products, compare prices, check delivery timelines, "
                "track orders, or take you straight to checkout."
            ),
            "quick_actions": quick_actions,
        }

    if any(term in text for term in ["help", "what can you do", "options", "support"]):
        return {
            "reply": (
                "I can help with product discovery, category browsing, cart and checkout questions, "
                "delivery and refund policies, and order tracking for signed-in customers."
            ),
            "quick_actions": [
                {"label": "Browse catalog", "url": "/"},
                {"label": "My wishlist", "url": "/wishlist/"},
                {"label": "Checkout", "url": "/checkout/"},
            ],
        }

    if any(term in text for term in ["cart", "basket"]):
        if cart_count_total:
            return {
                "reply": f"You currently have {cart_count_total} item{'s' if cart_count_total != 1 else ''} in your cart. You can review, update quantities, or continue to checkout.",
                "quick_actions": [
                    {"label": "Open cart", "url": "/cart/"},
                    {"label": "Checkout", "url": "/checkout/"},
                ],
            }
        return {
            "reply": "Your cart is empty right now. I can help you find herbal products to add based on wellness need, category, or budget.",
            "quick_actions": [
                {"label": "Shop catalog", "url": "/"},
                {"label": "Immunity products", "text": "show immunity products"},
                {"label": "Hair care", "text": "show hair care products"},
            ],
        }

    if any(term in text for term in ["checkout", "payment", "pay", "cod", "cash on delivery", "razorpay"]):
        return {
            "reply": (
                "You can place orders with Cash on Delivery or online payment. The checkout flow uses your saved default address, and online payments are processed through Razorpay."
            ),
            "quick_actions": [
                {"label": "Go to checkout", "url": "/checkout/"},
                {"label": "Saved addresses", "url": "/my-address/"},
            ],
        }

    if any(term in text for term in ["delivery", "shipping", "when will i get", "arrival", "arrive"]):
        if request.user.is_authenticated:
            latest_order = Order.objects.filter(user=request.user).order_by("-created_at").first()
            if latest_order:
                if latest_order.estimated_delivery:
                    estimate = latest_order.estimated_delivery.strftime("%b %d, %Y")
                    time_window = latest_order.estimated_delivery_time or "during the day"
                    return {
                        "reply": (
                            f"Your latest order is currently marked as {latest_order.tracking_status.lower()}. "
                            f"The estimated delivery is {estimate} {time_window}."
                        ),
                        "quick_actions": [
                            {"label": "View latest order", "url": f"/order/{latest_order.id}/"},
                            {"label": "Track all orders", "url": "/my-orders/"},
                        ],
                    }

        return {
            "reply": "Standard delivery usually takes about 3 to 5 working days, and Bangalore orders can receive tighter time windows depending on the saved address.",
            "quick_actions": [
                {"label": "Track orders", "url": "/my-orders/"},
                {"label": "Saved addresses", "url": "/my-address/"},
            ],
        }

    if any(term in text for term in ["refund", "return", "cancel order", "cancel my order", "cancellation"]):
        return {
            "reply": (
                "Orders can be cancelled until they are delivered. Paid orders move into refund processing after cancellation, while delivered orders can no longer be cancelled from the store panel."
            ),
            "quick_actions": [
                {"label": "My orders", "url": "/my-orders/"},
                {"label": "Track an order", "text": "track my order"},
            ],
        }

    if any(term in text for term in ["track", "order status", "my order", "where is my order"]):
        if request.user.is_authenticated:
            latest_order = Order.objects.filter(user=request.user).order_by("-created_at").first()
            if latest_order:
                return {
                    "reply": (
                        f"Your latest order #{latest_order.id} is currently {latest_order.tracking_status.lower()} "
                        f"and the current location is {latest_order.current_location}."
                    ),
                    "quick_actions": [
                        {"label": "Open order", "url": f"/order/{latest_order.id}/"},
                        {"label": "All orders", "url": "/my-orders/"},
                    ],
                }
        return {
            "reply": "Please sign in to track your personal orders. Once signed in, the My Orders page will show live status, timeline, and delivery estimate.",
            "quick_actions": [
                {"label": "Log in", "url": "/login/"},
                {"label": "My orders", "url": "/my-orders/"},
            ],
        }

    if any(term in text for term in ["wishlist", "saved items", "favorites", "favourites"]):
        if request.user.is_authenticated:
            wishlist_total = Wishlist.objects.filter(user=request.user).count()
            return {
                "reply": f"You currently have {wishlist_total} item{'s' if wishlist_total != 1 else ''} saved in your wishlist.",
                "quick_actions": [
                    {"label": "Open wishlist", "url": "/wishlist/"},
                    {"label": "Shop more", "url": "/"},
                ],
            }
        return {
            "reply": "You can save products to your wishlist after logging in, which makes it easier to compare and buy later.",
            "quick_actions": [
                {"label": "Log in", "url": "/login/"},
                {"label": "Browse products", "url": "/"},
            ],
        }

    if category_match or any(term in text for term in ["category", "categories", "collection", "collections"]):
        if category_match:
            category_products = Product.objects.filter(category=category_match).select_related("category")[:3]
            return {
                "reply": f"I found the {category_match.name} category. Here are a few related products from that collection.",
                "products": [_format_product_brief(product) for product in category_products],
                "quick_actions": [
                    {"label": f"Open {category_match.name}", "url": f"/category/{category_match.id}/"},
                    {"label": "Browse all categories", "url": "/"},
                ],
            }
        reply = "You can browse the store by category. Current collections include " + ", ".join(categories[:5]) + "."
        return {
            "reply": reply,
            "quick_actions": [{"label": name, "url": f"/search/?q={name}"} for name in categories[:3]],
        }

    wellness_map = {
        "hair": ["hair", "dandruff", "scalp", "oil", "serum", "shampoo"],
        "skin": ["skin", "face", "glow", "cream", "mask", "soap", "lotion"],
        "immunity": ["immunity", "immune", "giloy", "tulsi", "chyawanprash", "ashwagandha"],
        "digestion": ["digestion", "digestive", "gas", "detox", "liver"],
        "baby": ["baby", "kids", "infant"],
    }

    for intent_name, keywords in wellness_map.items():
        if any(keyword in text for keyword in keywords):
            intent_matches = Product.objects.filter(
                Q(name__icontains=intent_name) |
                Q(description__icontains=intent_name) |
                Q(category__name__icontains=intent_name)
            ).select_related("category")[:3]
            if intent_matches:
                return {
                    "reply": f"I found a few {intent_name}-focused options that should be a good place to start.",
                    "products": [_format_product_brief(product) for product in intent_matches],
                    "quick_actions": [
                        {"label": "View all products", "url": "/"},
                        {"label": "Search more", "url": f"/search/?q={intent_name}"},
                    ],
                }

    if matched_products:
        lead = matched_products[0]
        response = {
            "reply": f"I found products related to your question. The closest match is {lead.name} in {lead.category.name if lead.category else 'Herbal care'}.",
            "products": [_format_product_brief(product) for product in matched_products],
            "quick_actions": [
                {"label": "Open product", "url": f"/product/{lead.id}/"},
                {"label": "Search results", "url": f"/search/?q={lead.name}"},
            ],
        }
        return response

    return {
        "reply": (
            "I could not find an exact answer for that yet. Try asking with a product name, category, or a direct question like price, stock, delivery, refund, or order status."
        ),
        "quick_actions": [
            {"label": "Ask about a product", "text": "what is the price of tulsi drops"},
            {"label": "Track my order", "text": "track my order"},
            {"label": "Browse store", "url": "/"},
        ],
    }


@csrf_exempt
def support_chat(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST is allowed."}, status=405)

    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON payload."}, status=400)

    message = (payload.get("message") or "").strip()
    if not message:
        return JsonResponse({"error": "Message is required."}, status=400)

    return JsonResponse(_build_chat_response(request, message))


# ================= CONTEXT =================
def cart_count(request):
    cart = request.session.get("cart", {})
    wishlist_count = 0

    if request.user.is_authenticated:
        wishlist_count = Wishlist.objects.filter(user=request.user).count()

    return {
        "cart_count": sum(cart.values()),
        "wishlist_count": wishlist_count,
    }
