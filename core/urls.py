from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.site_search, name='site_search'),
    path('autocomplete/', views.autocomplete_search, name='autocomplete_search'),
]
