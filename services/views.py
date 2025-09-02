from django.shortcuts import render, get_object_or_404
from .models import Service
from django.core.paginator import Paginator

def service_list(request):
    services_list = Service.objects.all()
    paginator = Paginator(services_list, 6)
    page_number = request.GET.get('page')
    services = paginator.get_page(page_number)
    return render(request, 'services/service_list.html', {'services': services})

def service_detail(request, slug):
    service = get_object_or_404(Service, slug=slug)
    return render(request, 'services/service_detail.html', {'service': service})
