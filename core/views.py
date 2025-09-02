from django.shortcuts import render, redirect
from django.db.models import Q
from django.http import JsonResponse
from shop.models import Product, Pet, Store  # Import models from shop


# --------------------------
# Utility: plural/singular handling
# --------------------------
def normalize_term(term):
    """Return basic plural/singular variations."""
    if term.endswith('s'):
        return [term[:-1], term]
    else:
        return [term, term + 's']


# --------------------------
# Main Site Search
# --------------------------
def site_search(request):
    query = request.GET.get('q', '').strip().lower()
    keywords = query.split()

    # --- Redirect for generic keywords ---
    if query in ['pet products', 'products', 'pet product']:
        return redirect('shop:all_products')  # all products page
    if query in ['pet store', 'store', 'stores']:
        return redirect('shop:store')  # store landing page

    # --- Redirect for exact / partial store name ---
    matching_store = Store.objects.filter(name__iexact=query).first()
    if not matching_store:
        matching_store = Store.objects.filter(name__icontains=query).first()
    if matching_store:
        return redirect('shop:store_detail', pk=matching_store.pk)

    # --- Known filter keywords ---
    pet_keywords = ['dog', 'cat', 'bird', 'fish', 'rabbit']
    category_keywords = ['accessories', 'food', 'medicine', 'medicines', 'cage', 'toy']

    pet_filter = None
    category_filter = None

    for kw in keywords:
        if kw in pet_keywords:
            pf = Q(category__pet_category__name__icontains=kw)
            pet_filter = pf if pet_filter is None else pet_filter | pf
        if kw in category_keywords:
            cf = Q(category__name__icontains=kw)
            category_filter = cf if category_filter is None else category_filter | cf

    # --- Product filtering logic ---
    if pet_filter and category_filter:
        product_filter = pet_filter & category_filter
    elif pet_filter:
        product_filter = pet_filter
    elif category_filter:
        product_filter = category_filter
    else:
        # Fallback: search by each term (partial support)
        product_filter = Q()
        for t in keywords:
            product_filter |= Q(name__icontains=t) | Q(category__name__icontains=t)

    products = Product.objects.filter(product_filter).distinct()

    # --- Pets search ---
    pet_name_filter = Q()
    for t in keywords:
        pet_name_filter |= Q(name__icontains=t)
    pets = Pet.objects.filter(pet_name_filter).distinct()

    # --- Stores search ---
    store_name_filter = Q()
    for t in keywords:
        store_name_filter |= Q(name__icontains=t)
    stores = Store.objects.filter(store_name_filter).distinct()

    return render(request, 'core/site_search_results.html', {
        'query': query,
        'products': products,
        'pets': pets,
        'stores': stores
    })


# --------------------------
# Autocomplete Search
# --------------------------
def autocomplete_search(request):
    term = request.GET.get('term', '').strip().lower()
    results = []

    if term:
        keywords = term.split()

        pet_keywords = ['dog', 'cat', 'bird', 'fish', 'rabbit']
        category_keywords = ['accessories', 'food', 'medicine', 'medicines', 'cage', 'toy']

        pet_filter = None
        category_filter = None

        for kw in keywords:
            if kw in pet_keywords:
                pf = Q(category__pet_category__name__icontains=kw)
                pet_filter = pf if pet_filter is None else pet_filter | pf
            if kw in category_keywords:
                cf = Q(category__name__icontains=kw)
                category_filter = cf if category_filter is None else category_filter | cf

        if pet_filter and category_filter:
            product_filter = pet_filter & category_filter
        elif pet_filter:
            product_filter = pet_filter
        elif category_filter:
            product_filter = category_filter
        else:
            # Partial match fallback on each keyword
            product_filter = Q()
            for t in keywords:
                product_filter |= Q(name__icontains=t) | Q(category__name__icontains=t)

        # --- Products autocomplete ---
        products = Product.objects.filter(product_filter).distinct()[:5]
        for p in products:
            results.append({'label': f'Product: {p.name}', 'url': p.get_absolute_url()})

        # --- Pets autocomplete ---
        pet_name_filter = Q()
        for t in keywords:
            pet_name_filter |= Q(name__icontains=t)
        pets = Pet.objects.filter(pet_name_filter).distinct()[:3]
        for pet in pets:
            results.append({'label': f'Pet: {pet.name}', 'url': pet.get_absolute_url()})

        # --- Stores autocomplete ---
        store_name_filter = Q()
        for t in keywords:
            store_name_filter |= Q(name__icontains=t)
        stores = Store.objects.filter(store_name_filter).distinct()[:3]
        for store in stores:
            results.append({'label': f'Store: {store.name}', 'url': f"/store/{store.pk}/"})

    return JsonResponse(results, safe=False)
