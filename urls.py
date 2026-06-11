from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from .views import admin_dashboard

urlpatterns = [
    path('', views.home, name='home'),
    path('help/', views.help_support, name='help_support'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='books/login.html'), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('add-to-cart/<int:book_id>/', views.add_to_cart, name='add_to_cart'),
    path('remove-from-cart/<int:book_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/', views.view_cart, name='view_cart'),
    path('place-order/', views.place_order_cart, name='place_order_cart'),
    path('orders/', views.order_history, name='order_history'),
    path('order/<int:book_id>/', views.place_order_single, name='place_order'),
    path('book/<int:book_id>/', views.book_detail, name='book_detail'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('make-payment/', views.make_payment, name='make_payment'),
    path('payment-success/', views.payment_success, name='payment_success'),
    path('make-payment/<int:book_id>/', views.make_payment, name='make_payment_single'),
    path('ebook/buy/<int:book_id>/', views.buy_ebook, name='buy_ebook'),
    path('ebook/verify/<int:book_id>/', views.ebook_payment_verify, name='ebook_payment_verify'),
    path('ebook/download/<int:book_id>/', views.download_ebook, name='download_ebook'),
]
