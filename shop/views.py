from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.contrib.contenttypes.models import ContentType

from .models import Pet, PetCategory, ProductCategory, Product, Store, Favourite, PetReview,Order
from wishlist.models import WishlistItem  # adjust import path if different
from django.contrib import messages
from django.views.decorators.http import require_POST
# from carts.utils import _cart_id
from carts.models import Cart, CartItem
from django.db.models import Count, Q
from urllib.parse import urlencode


def pet_store_home(request):
    """
    Display list of pets with optional category filtering and pagination.
    """
    categories = PetCategory.objects.all()
    selected_category = request.GET.get('category')
    pets = Pet.objects.all()

    if selected_category:
        pets = pets.filter(category_id=selected_category)

    paginator = Paginator(pets, 4)  # 4 pets per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'categories': categories,
        'pets': page_obj,
        'selected_category': selected_category,
        'page_obj': page_obj,
    }
    return render(request, 'shop/store.html', context)

def pet_detail(request, pk):
    """
    Detail view of a pet including related products, reviews, wishlist and in-cart status.
    """
    pet = get_object_or_404(Pet, pk=pk)

    # Fetch all product categories for this pet's category
    product_categories = ProductCategory.objects.filter(pet_category=pet.category)

    accessory_pet = product_categories.filter(name__istartswith='Accessories')
    accessories = Product.objects.filter(category__in=accessory_pet).distinct()[:6]
    related_products = Product.objects.filter(category__pet_category=pet.category)
    print("Related Products total count:", related_products.count())

    # Prepare reviews (approved and ordered)
    reviews = pet.reviews.filter(approved=True).order_by('-created_at')

    # Wishlist status for current user (generic wishlist)
    is_in_wishlist = False
    if request.user.is_authenticated:
        content_type = ContentType.objects.get_for_model(pet)
        is_in_wishlist = WishlistItem.objects.filter(
            user=request.user,
            content_type=content_type,
            object_id=pet.id
        ).exists()

    # Get or find cart (user or session)
    cart = None
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
    if not cart:
        cart = Cart.objects.filter(cart_id=_cart_id(request)).first()

    in_cart = False
    if cart:
        content_type = ContentType.objects.get_for_model(pet)
        in_cart = CartItem.objects.filter(
            cart=cart,
            content_type=content_type,
            object_id=pet.id,
            active=True
        ).exists()

    context = {
        'pet': pet,
        'accessories': accessories,
        'related_products': related_products,
        'reviews': reviews,
        'average_rating': pet.average_rating,
        'review_count': pet.review_count,
        'is_in_wishlist': is_in_wishlist,
        'in_cart': in_cart,
    }
    return render(request, 'shop/pet_detail.html', context)



@login_required
def toggle_favourite(request, pet_id):
    """
    If you want to keep favourite toggle for pets specifically (optional).
    Consider migrating to generic wishlist for all.
    """
    pet = get_object_or_404(Pet, pk=pet_id)
    favourite, created = Favourite.objects.get_or_create(user=request.user, pet=pet)
    if not created:
        favourite.delete()
        favorited = False
    else:
        favorited = True
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'favorited': favorited})
    return redirect('shop:pet_detail', pk=pet_id)


@login_required
def add_pet_review(request, pet_id):
    """
    Handle POST request to add a review for a pet.
    """
    pet = get_object_or_404(Pet, pk=pet_id)

    if request.method == 'POST':
        rating = int(request.POST.get('rating', 0))
        title = request.POST.get('title', '').strip()
        comment = request.POST.get('comment', '').strip()

        if rating and title and comment:
            PetReview.objects.create(
                pet=pet,
                user=request.user,
                rating=rating,
                comment=comment,
                approved=False,  # Requires admin approval
            )
            return redirect('shop:pet_detail', pk=pet.pk)
        else:
            context = {
                'pet': pet,
                'error': 'Please fill in all fields.',
                'reviews': pet.reviews.filter(approved=True).order_by('-created_at'),
            }
            return render(request, 'shop/pet_detail.html', context)
    else:
        return redirect('shop:pet_detail', pk=pet.pk)


def store_detail(request, pk):
    """
    View to see store details including pets and products.
    """
    store = get_object_or_404(Store, pk=pk)
    pets = store.pets.all()
    products = store.products.all()

    context = {
        'store': store,
        'pets': pets,
        'products': products,
    }
    return render(request, 'shop/store_detail.html', context)

def _cart_id(request):
    cart_id = request.session.session_key
    if not cart_id:
        request.session.create()
        cart_id = request.session.session_key
    return cart_id

def checkout(request):
    item = None
    is_single_item = False
    cart_items = []
    total = 0
    quantity = 0
    item_model = ''
    item_id = request.GET.get('item_id')
    model_name = request.GET.get('model')

    CARTABLE_MODELS = {'pet': Pet, 'product': Product}

    if model_name and item_id:
        # Buy now single item
        model = CARTABLE_MODELS.get(model_name)
        if model:
            item = get_object_or_404(model, pk=item_id)
            is_single_item = True
            item_model = model_name
            total = item.price
            quantity = 1
        else:
            messages.error(request, "Invalid item specified.")
            return redirect('shop:store')
    else:
        # Cart checkout
        if request.user.is_authenticated:
            cart = Cart.objects.filter(user=request.user).first()
        else:
            cart = Cart.objects.filter(cart_id=_cart_id(request)).first()

        if not cart:
            messages.error(request, "You have no active cart.")
            return redirect('shop:store')

        cart_items = CartItem.objects.filter(cart=cart, active=True)

        if not cart_items.exists():
            messages.error(request, "Your cart is empty.")
            return redirect('shop:store')

        total = sum(ci.subtotal() for ci in cart_items)
        quantity = sum(ci.quantity for ci in cart_items)

    context = {
        'is_single_item': is_single_item,
        'item': item,
        'item_model': item_model,
        'item_id': item_id,
        'cart_items': cart_items,
        'total': total,
        'quantity': quantity,
    }
    return render(request, 'shop/checkout.html', context)


# @require_POST
# def process_order(request):
#     is_single_item = request.POST.get('is_single_item') == 'True'

#     buyer_name = request.POST.get('buyer_name')
#     email = request.POST.get('email')
#     phone = request.POST.get('phone')
#     shipping_address = request.POST.get('shipping_address')
#     payment_method = request.POST.get('payment_method')
#     user_upi_id = request.POST.get('user_upi_id')  # Optional, only for UPI payment

#     if not all([buyer_name, email, phone, shipping_address, payment_method]):
#         messages.error(request, "Please fill all required fields.")
#         return redirect('shop:checkout')

#     # For single item order
#     if is_single_item:
#         model = request.POST.get('item_model')
#         item_id = request.POST.get('item_id')
#         CARTABLE_MODELS = {'pet': Pet, 'product': Product}
#         model_cls = CARTABLE_MODELS.get(model)

#         if not model_cls:
#             messages.error(request, "Invalid item specified.")
#             return redirect('shop:checkout')

#         try:
#             item = model_cls.objects.get(pk=item_id)
#         except model_cls.DoesNotExist:
#             messages.error(request, "Item not found.")
#             return redirect('shop:checkout')

#         order = Order.objects.create(
#             item_name=item.name,
#             buyer_name=buyer_name,
#             email=email,
#             phone=phone,
#             shipping_address=shipping_address,
#             payment_method=payment_method,
#             user_upi_id=user_upi_id if payment_method == 'upi' else None,
#         )
#         order_amount = float(item.price)  # make sure your model has price field

#     # For cart order
#     else:
#         cart = Cart.objects.filter(cart_id=_cart_id(request)).first()
#         if not cart:
#             messages.error(request, "You have no active cart.")
#             return redirect('shop:checkout')

#         cart_items = CartItem.objects.filter(cart=cart, active=True)
#         if not cart_items.exists():
#             messages.error(request, "Your cart is empty.")
#             return redirect('shop:checkout')

#         order = Order.objects.create(
#             item_name=f"Cart order with {cart_items.count()} items",
#             buyer_name=buyer_name,
#             email=email,
#             phone=phone,
#             shipping_address=shipping_address,
#             payment_method=payment_method,
#             user_upi_id=user_upi_id if payment_method == 'upi' else None,
#         )
#         order_amount = sum(ci.subtotal for ci in cart_items)

#         # Mark cart items inactive after order placed
#         cart_items.update(active=False)

#     # If payment method is UPI, generate UPI URI and display redirect page
#     if payment_method == 'upi':
#         merchant_upi_id = 'your-merchant-upi@bank'  # Replace with your actual UPI ID
#         payee_name = 'Pawverse Store'
#         transaction_ref = f"ORDER{order.id}"
#         txn_note = f"Payment for order {order.id}"
#         amount_str = f"{order_amount:.2f}"

#         params = {
#             "pa": merchant_upi_id,
#             "pn": payee_name,
#             "tr": transaction_ref,
#             "tn": txn_note,
#             "am": amount_str,
#             "cu": "INR",
#         }
#         upi_uri = "upi://pay?" + urlencode(params)

#         # Optionally generate QR code URL here and pass to template
#         qr_code_url = None  # TODO: implement QR code generation if you like

#         context = {
#             "upi_uri": upi_uri,
#             "qr_code_url": qr_code_url,
#             "order_id": order.id,
#         }
#         return render(request, "shop/upi_redirect.html", context)

#     # For other payment methods, display success page after order placed
#     messages.success(request, "Order placed successfully!")
#     return redirect('shop:order_success')

@require_POST
def process_order(request):
    is_single_item = request.POST.get('is_single_item') == 'True'

    buyer_name = request.POST.get('buyer_name')
    email = request.POST.get('email')
    phone = request.POST.get('phone')
    shipping_address = request.POST.get('shipping_address')
    payment_method = request.POST.get('payment_method')
    user_upi_id = request.POST.get('user_upi_id')  # Optional, only for UPI payment

    if not all([buyer_name, email, phone, shipping_address, payment_method]):
        messages.error(request, "Please fill all required fields.")
        return redirect('shop:checkout')

    CARTABLE_MODELS = {'pet': Pet, 'product': Product}

    # Handle single item order (buy now)
    if is_single_item:
        model = request.POST.get('item_model')
        item_id = request.POST.get('item_id')
        model_cls = CARTABLE_MODELS.get(model)

        if not model_cls:
            messages.error(request, "Invalid item specified.")
            return redirect('shop:checkout')

        try:
            item = model_cls.objects.get(pk=item_id)
        except model_cls.DoesNotExist:
            messages.error(request, "Item not found.")
            return redirect('shop:checkout')

        order = Order.objects.create(
            item_name=item.name,
            buyer_name=buyer_name,
            email=email,
            phone=phone,
            shipping_address=shipping_address,
            payment_method=payment_method,
            user_upi_id=user_upi_id if payment_method == 'upi' else None,
        )
        order_amount = float(item.price)  # Assume price field exists

    # Handle cart order
    else:
        if request.user.is_authenticated:
            cart = Cart.objects.filter(user=request.user).first()
        else:
            cart = Cart.objects.filter(cart_id=_cart_id(request)).first()

        if not cart:
            messages.error(request, "You have no active cart.")
            return redirect('shop:checkout')

        cart_items = CartItem.objects.filter(cart=cart, active=True)
        if not cart_items.exists():
            messages.error(request, "Your cart is empty.")
            return redirect('shop:checkout')

        order = Order.objects.create(
            item_name=f"Cart order with {cart_items.count()} items",
            buyer_name=buyer_name,
            email=email,
            phone=phone,
            shipping_address=shipping_address,
            payment_method=payment_method,
            user_upi_id=user_upi_id if payment_method == 'upi' else None,
        )
        order_amount = sum(ci.subtotal() for ci in cart_items)

        # Mark cart items inactive after order placed
        cart_items.update(active=False)

    # Handle UPI payment method with intent URI
    if payment_method == 'upi':
        merchant_upi_id = 'your-merchant-upi@bank'  # Replace with your actual UPI ID
        payee_name = 'Pawverse Store'
        transaction_ref = f"ORDER{order.id}"
        txn_note = f"Payment for order {order.id}"
        amount_str = f"{order_amount:.2f}"

        params = {
            "pa": merchant_upi_id,
            "pn": payee_name,
            "tr": transaction_ref,
            "tn": txn_note,
            "am": amount_str,
            "cu": "INR",
        }
        upi_uri = "upi://pay?" + urlencode(params)

        # Optionally generate QR code URL here and pass to template
        qr_code_url = None  # Implement QR code generation if desired

        context = {
            "upi_uri": upi_uri,
            "qr_code_url": qr_code_url,
            "order_id": order.id,
        }
        return render(request, "shop/upi_redirect.html", context)

    # For other payment methods redirect to success page after order placed
    messages.success(request, "Order placed successfully!")
    return redirect('shop:order_success')

def order_success(request):
    return render(request, 'shop/order_success.html')

def product_list_by_category(request, category_slug):
    category = get_object_or_404(ProductCategory, slug=category_slug)
    products_qs = Product.objects.filter(category=category).distinct()
    paginator = Paginator(products_qs, 4)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'category': category,
        'products': page_obj,
        'page_obj': page_obj,
        # Removed in_cart_product_ids since no cart buttons are used in template
    }
    return render(request, 'shop/product_list_by_category.html', context)


def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)

    # -------------------
    # Check cart (auth / guest)
    # -------------------
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
    else:
        cart = Cart.objects.filter(cart_id=_cart_id(request)).first()

    in_cart = False
    if cart:
        in_cart = CartItem.objects.filter(
            cart=cart,
            active=True,
            content_type=ContentType.objects.get_for_model(Product),
            object_id=product.id
        ).exists()

    # -------------------
    # Check wishlist (auth only)
    # -------------------
    is_in_wishlist = False
    if request.user.is_authenticated:
        is_in_wishlist = WishlistItem.objects.filter(
            user=request.user,
            content_type=ContentType.objects.get_for_model(Product),
            object_id=product.id
        ).exists()

    # -------------------
    # Context
    # -------------------
    context = {
        'product': product,
        'in_cart': in_cart,                  # For Add to Cart button state
        'is_in_wishlist': is_in_wishlist     # For Wishlist heart state
    }
    return render(request, 'shop/product_detail.html', context)


def product_category_list(request):
    """
    Show all product categories with pagination (4 per page).
    """
    categories_qs = ProductCategory.objects.select_related('pet_category').all()
    paginator = Paginator(categories_qs, 4)  # Show 4 categories per page

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'categories': page_obj,  # use paginated object
        'page_obj': page_obj,
    }
    return render(request, 'shop/category_list.html', context)

def accessories_all_pets(request):
    # All accessory categories
    accessories_categories = ProductCategory.objects.filter(name__icontains='Accessories')

    # Fetch all products belonging to these categories
    products = Product.objects.filter(category__in=accessories_categories)

    context = {
        'accessories_categories': accessories_categories,  # for sidebar links
        'products': products,
    }
    return render(request, 'shop/accessories_all_pets.html', context)

def medicines_all_pets(request):
    # Get all medicine categories for any pet (match singular/plural)
    medicines_categories = (
        ProductCategory.objects
        .filter(Q(name__icontains='Medicine') | Q(name__icontains='Medicines'))
        .annotate(product_count=Count('product'))
        .filter(product_count__gt=0)   # only categories with products
    )

    # All products in those categories
    products = Product.objects.filter(category__in=medicines_categories)

    return render(request, 'shop/medicines_all_pets.html', {
        'medicines_categories': medicines_categories,
        'products': products
    })

def food_all_pets(request):
    # Get all food categories for any pet
    food_categories = (
        ProductCategory.objects
        .filter(Q(name__icontains='Food') | Q(name__icontains='Foods'))
        .annotate(product_count=Count('product'))
        .filter(product_count__gt=0)   # Only categories with products
    )

    # All products in those categories
    products = Product.objects.filter(category__in=food_categories)

    return render(request, 'shop/food_all_pets.html', {
        'food_categories': food_categories,
        'products': products
    })

def all_products(request):
    selected_category = request.GET.get('category', '')

    # Base queryset - latest first
    products_qs = Product.objects.all().order_by('-id')

    # Category filters
    if selected_category == 'accessories_toys':
        products_qs = products_qs.filter(
            Q(category__name__icontains='Accessories') |
            Q(category__name__icontains='Toys')
        )
    elif selected_category == 'medicines':
        products_qs = products_qs.filter(category__name__icontains='Medicine')
    elif selected_category == 'food':
        products_qs = products_qs.filter(category__name__icontains='Food')
    elif selected_category == 'cages':
        products_qs = products_qs.filter(category__name__icontains='Cage')
    elif selected_category == 'aquarium_supplies':
        products_qs = products_qs.filter(
            Q(category__name__icontains='Aquarium') |
            Q(category__name__icontains='Tank')
        )

    # Pagination: 6 products per page
    paginator = Paginator(products_qs, 6)
    page_number = request.GET.get('page')
    products_page = paginator.get_page(page_number)

    context = {
        'products': products_page,            # paginated list
        'selected_category': selected_category
    }
    return render(request, 'shop/all_products.html', context)


def bird_cages(request):
    # Find categories that are cages for birds
    cage_categories = ProductCategory.objects.filter(
        pet_category__name__iexact='Birds',
        name__icontains='Cage'
    )
    products = Product.objects.filter(category__in=cage_categories)

    return render(request, 'shop/cages_birds.html', {
        'products': products,
        'selected_category': 'bird_cages'
    })

def fish_aquarium_supplies(request):
    # Find categories for Aquarium Supplies for Fish
    aquarium_categories = ProductCategory.objects.filter(
        pet_category__name__iexact='Fish'
    ).filter(name__icontains='Aquarium')
    
    products = Product.objects.filter(category__in=aquarium_categories)

    return render(request, 'shop/aquarium_supplies_fish.html', {
        'products': products,
        'selected_category': 'fish_aquarium_supplies'
    })

def all_pet_shops(request):
    stores_list = Store.objects.all().order_by('name')  # optionally order alphabetically
    paginator = Paginator(stores_list, 6)  # 6 shops per page

    page_number = request.GET.get('page')
    stores = paginator.get_page(page_number)

    return render(request, 'shop/all_pet_shops.html', {
        'stores': stores
    })

@require_POST
def confirm_upi_payment(request, order_id):
    # Here you would typically:
    # - verify payment status (manually or via gateway)
    # - update order status in database
    # For now, just a placeholder implementation

    # Mark order paid or handle verification
    # order = Order.objects.get(pk=order_id)
    # order.payment_status = 'paid'  # customize as needed
    # order.save()

    messages.success(request, "Thank you! Your UPI payment confirmation has been received.")
    return redirect('shop:order_success')  # Or any success page you have
