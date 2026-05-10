from django.urls import path
from . import views

urlpatterns = [

    path('', views.home, name='home'),
    path('search/', views.search, name='search'),
    path('category/<int:id>/', views.category_products, name='category_products'),
    path('product/<int:id>/', views.product_detail, name='product_detail'),

    path('add-review/<int:product_id>/', views.add_review, name='add_review'),

    path('cart/', views.cart, name='cart'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('increase/<int:product_id>/', views.increase_cart, name='increase_cart'),
    path('decrease/<int:product_id>/', views.decrease_cart, name='decrease_cart'),
    path('remove-from-cart/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('verify-payment/', views.verify_payment, name='verify_payment'),
    path('support-chat/', views.support_chat, name='support_chat'),
    path('checkout/', views.checkout, name='checkout'),
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),
    path('my-orders/', views.my_orders, name='my_orders'),
    path('cancel-order/<int:order_id>/', views.cancel_order, name='cancel_order'),
    path('wishlist/', views.wishlist, name='wishlist'),
    path('add-to-wishlist/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('remove-from-wishlist/<int:product_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    path('move-wishlist-to-cart/<int:product_id>/', views.move_wishlist_to_cart, name='move_wishlist_to_cart'),
    path('profile/', views.profile, name='profile'),
    path('my-address/', views.my_address, name='my_address'),
    path('create-payment/', views.create_payment, name='create_payment'),
    path('login/', views.send_otp, name='login'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),
]
