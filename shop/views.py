from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Product, Cart, Order, Review, CustomUser
from .forms import RegisterForm, LoginForm, ReviewForm, ProfileForm
from django.core.mail import send_mail
from django.conf import settings
#from sslcommerz_python.payment import SSLCSession
from sslcommerz_python_api import SSLCSession
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse


from decimal import Decimal
from .utils import send_verification_email, verify_token

from django.contrib.auth import get_user_model
User = get_user_model()

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
            messages.success(request, 'Check your email for verification.')
            return redirect('login')
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})
# verify email
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
def update_cart(request):
    if request.method == 'POST':
        cart_items = Cart.objects.filter(user=request.user)
        for item in cart_items:
            quantity_key = f'quantity_{item.id}'
            try:
                quantity = int(request.POST.get(quantity_key))
                if quantity > 0:
                    item.quantity = quantity
                    item.save()
                else:
                    item.delete()  # delete item if quantity is 0
            except (ValueError, TypeError):
                continue
    return redirect('cart')


@login_required
def cart_view(request):
    cart_items = Cart.objects.filter(user=request.user)
    total = sum(item.product.new_price * item.quantity for item in cart_items)
    return render(request, 'cart.html', {'cart_items': cart_items, 'total': total})



def checkout(request):
    mypayment = SSLCSession(
        sslc_is_sandbox=True,
        sslc_store_id="alsal681df9d4ec806",
        sslc_store_pass="alsal681df9d4ec806@ssl",
    )

    status_url = request.build_absolute_uri("sslc/status")

    mypayment.set_urls(
        success_url=status_url,
        fail_url=status_url,
        cancel_url=status_url,
        ipn_url=status_url,
    )

    
    mypayment.set_product_integration(
        total_amount=100.00,
        currency='BDT',
        product_category='clothing',
        product_name='T-shirt',
        num_of_item=1,
        shipping_method='Courier',
        product_profile='general'
    )

    mypayment.set_customer_info(
        name='Test Customer',
        email='test@example.com',
        address1='Dhaka',
        address2='Dhaka',
        city='Dhaka',
        postcode='1216',
        country='Bangladesh',
        phone='01711111111'
    )

    mypayment.set_shipping_info(
        shipping_to='Customer Name',
        address='Dhaka',
        city='Dhaka',
        postcode='1216',
        country='Bangladesh'
    )

    mypayment.set_additional_values(
        value_a=str(request.user.id)
    )

    response_data = mypayment.init_payment()

    
    if response_data.get('status') == 'SUCCESS':
        return redirect(response_data['GatewayPageURL'])
    else:
        return HttpResponse(f"SSLCommerz Error: {response_data}", status=400)

@csrf_exempt
def sslc_status(request):
    if request.method == 'POST':
        data = request.POST
        status = data.get('status')

        if status == 'VALID':
            user_id = data.get('value_a')
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return JsonResponse({'error': 'User not found'}, status=404)

            cart_items = Cart.objects.filter(user=user)
            for item in cart_items:
                Order.objects.create(
                    user=user,
                    product=item.product,
                    quantity=item.quantity,
                    total_price=item.product.new_price * item.quantity,
                    is_paid=True
                )
                item.product.stock -= item.quantity
                item.product.save()
            cart_items.delete()
            return JsonResponse({'status': 'Payment success, order placed'}, status=200)

        return JsonResponse({'status': 'Payment not valid'}, status=400)

    return JsonResponse({'error': 'Invalid method'}, status=405)



# Dashboard

@login_required
def dashboard(request):
    user = request.user
    orders = Order.objects.filter(user=user).order_by('-created_at')[:5]
    reviews = Review.objects.filter(user=user).order_by('-created_at')[:5]

    return render(request, 'dashboard.html', {
        'user': user,
        'orders': orders,
        'reviews': reviews,
    })


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



def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect('login')  
