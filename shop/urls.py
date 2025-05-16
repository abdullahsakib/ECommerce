from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    path('cart/', views.cart_view, name='cart'),
    path('add-to-cart/<int:pk>/', views.add_to_cart, name='add_to_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='login'),
    #path('logout/', views.logout_view, name='logout'),
    path('checkout/sslc/status', views.sslc_status, name='sslc_status'),
    path('register/', views.register, name='register'),
    path('verify/<str:token>/', views.verify_email, name='verify_email'),
    path('product/<int:pk>/review/', views.review_create, name='submit_review'),
    path('profile/', views.profile_view, name='profile'),
]
