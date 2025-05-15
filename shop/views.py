from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Product, Cart, Order, Review, CustomUser
from .forms import RegisterForm, LoginForm, ReviewForm, ProfileForm
from django.core.mail import send_mail
from django.conf import settings
# from sslcommerz_python.payment import SSLCSession
from decimal import Decimal
from .utils import send_verification_email, verify_token

# Home view
def home(request):
    products = Product.objects.all()
    return render(request, 'home.html', {'products': products})

# Product detail view
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'product_detail.html', {'product': product})

# Register view
def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            send_verification_email(user)
            # send_mail(
            #     'Verify your account',
            #     'Please verify your email to activate your account.',
            #     settings.DEFAULT_FROM_EMAIL,
            #     [user.email],
            # )
            messages.success(request, 'Check your email for verification.')
            return redirect('login')
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})

def verify_email(request, token):
    user_id = verify_token(token)
    if user_id:
        user = CustomUser.objects.get(pk=user_id)
        user.is_active = True
        user.save()
        messages.success(request, 'Email verified! You can now log in.')
        return redirect('login')
    else:
        messages.error(request, 'Verification link expired or invalid.')
        return redirect('register')
    


# Login view
def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(email=form.cleaned_data['email'], password=form.cleaned_data['password'])
            if user and user.is_active:
                login(request, user)
                return redirect('home')
            messages.error(request, 'Invalid login.')
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})

# Cart views
@login_required
def add_to_cart(request, pk):
    product = get_object_or_404(Product, pk=pk)
    cart, created = Cart.objects.get_or_create(user=request.user, product=product)
    cart.quantity += 1
    cart.save()
    return redirect('cart')

@login_required
def cart_view(request):
    cart_items = Cart.objects.filter(user=request.user)
    total = sum(item.product.new_price * item.quantity for item in cart_items)
    return render(request, 'cart.html', {'cart_items': cart_items, 'total': total})

# # Checkout and payment
# @login_required
# def checkout(request):
#     cart_items = Cart.objects.filter(user=request.user)
#     if not cart_items:
#         return redirect('home')

#     total = sum(item.product.new_price * item.quantity for item in cart_items)

#     store_id = settings.SSLCOMMERZ_STORE_ID
#     store_pass = settings.SSLCOMMERZ_STORE_PASSWORD
#     mypayment = SSLCSession(sslc_is_sandbox=True, sslc_store_id=store_id, sslc_store_pass=store_pass)

#     mypayment.set_urls(
#         success_url=settings.SITE_URL + '/payment-success/',
#         fail_url=settings.SITE_URL + '/payment-fail/',
#         cancel_url=settings.SITE_URL + '/cart/'
#     )

#     mypayment.set_product_integration(
#         total_amount=Decimal(total),
#         currency='BDT',
#         product_category='Ecommerce',
#         product_name='Cart Order',
#         num_of_item=len(cart_items),
#         shipping_method='Courier',
#         product_profile='general'
#     )

#     mypayment.set_customer_info(
#         name=request.user.email,
#         email=request.user.email,
#         address1='N/A',
#         city='Dhaka',
#         postcode='1200',
#         country='Bangladesh',
#         phone='01234567890'
#     )

#     response_data = mypayment.init_payment()
#     return redirect(response_data['GatewayPageURL'])

# # Payment success
# @login_required
# def payment_success(request):
#     cart_items = Cart.objects.filter(user=request.user)
#     for item in cart_items:
#         Order.objects.create(
#             user=request.user,
#             product=item.product,
#             quantity=item.quantity,
#             total_price=item.product.new_price * item.quantity,
#             is_paid=True
#         )
#         item.product.stock -= item.quantity
#         item.product.save()
#     cart_items.delete()
#     messages.success(request, 'Payment successful! Order placed.')
#     return redirect('dashboard')

# Dashboard
@login_required
def dashboard(request):
    orders = Order.objects.filter(user=request.user)
    reviews = Review.objects.filter(user=request.user)
    return render(request, 'dashboard.html', {'orders': orders, 'reviews': reviews})

# Profile
@login_required
def profile_view(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated.')
    else:
        form = ProfileForm(instance=request.user)
    return render(request, 'profile.html', {'form': form})

# Review
@login_required
def review_create(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.product = product
            review.save()
            return redirect('product_detail', pk=pk)
    else:
        form = ReviewForm()
    return render(request, 'review_form.html', {'form': form})
