from django.shortcuts import render, get_object_or_404, redirect
from .models import Service,Booking, ServiceCenter
from django.core.paginator import Paginator
from .forms import BookingForm
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.mail import send_mail
from django.contrib import messages
from django.http import JsonResponse
import math

def service_list(request):
    services_list = Service.objects.all()
    paginator = Paginator(services_list, 6)
    page_number = request.GET.get('page')
    services = paginator.get_page(page_number)
    return render(request, 'services/service_list.html', {'services': services})

def service_detail(request, slug):
    service = get_object_or_404(Service, slug=slug)
    return render(request, 'services/service_detail.html', {'service': service})

@login_required
def book_service(request):
    service_id = request.GET.get('service')
    initial_data = {}
    if service_id:
        initial_data['service'] = service_id

    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.user = request.user
            if not booking.email:
                booking.email = request.user.email
            booking.save()

            # Send confirmation email
            subject = f"Booking Confirmation for {booking.service.title}"
            message = (
                f"Hello {booking.user.first_name},\n\n"
                f"Thank you for booking {booking.service.title}.\n"
                f"Details:\n"
                f"Date: {booking.booking_date}\n"
                f"Time: {booking.booking_time}\n"
                f"Pet Name: {booking.pet_name or 'N/A'}\n"
                f"Pet Type: {booking.pet_type or 'N/A'}\n\n"
                f"We will contact you if we need any more information.\n\n"
                f"Best regards,\nPawverse Team"
            )
            recipient_email = booking.email or booking.user.email

            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [recipient_email],
                fail_silently=False,
            )

            messages.success(request, 'Booking created! Please check your email for confirmation.')
            return redirect('services:booking_success')
    else:
        form = BookingForm(initial=initial_data)

    return render(request, 'services/book_service.html', {'form': form})


def booking_success(request):
    return render(request, 'services/booking_success.html')

@login_required
def booking_history(request):
    bookings = Booking.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'services/booking_history.html', {'bookings': bookings})


@login_required
def payment_success(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id, user=request.user)
    booking.is_paid = True
    booking.save()
    messages.success(request, 'Payment successful! Thank you.')
    return redirect('services:booking_history')

def nearby_service_centers(request):
    try:
        lat = float(request.GET.get('lat'))
        lng = float(request.GET.get('lng'))
        radius_km = float(request.GET.get('radius', 10))  # default 10km radius
    except (TypeError, ValueError):
        return JsonResponse({'error': 'Invalid parameters'}, status=400)

    centers = ServiceCenter.objects.all()
    nearby_centers = []

    # Simple radius filter using haversine formula
    def haversine(lat1, lon1, lat2, lon2):
        R = 6371  # Earth radius in km
        d_lat = math.radians(lat2 - lat1)
        d_lon = math.radians(lon2 - lon1)
        a = (math.sin(d_lat / 2) ** 2 +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(d_lon / 2) ** 2)
        c = 2 * math.asin(math.sqrt(a))
        return R * c

    for center in centers:
        distance = haversine(lat, lng, float(center.latitude), float(center.longitude))
        if distance <= radius_km:
            nearby_centers.append({
                'id': center.id,
                'name': center.name,
                'address': center.address,
                'latitude': str(center.latitude),
                'longitude': str(center.longitude),
                'distance_km': round(distance, 2),
            })

    nearby_centers = sorted(nearby_centers, key=lambda x: x['distance_km'])
    return JsonResponse({'centers': nearby_centers})