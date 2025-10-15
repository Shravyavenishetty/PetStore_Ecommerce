from django import forms
from .models import Booking,Service

class BookingForm(forms.ModelForm):
    service = forms.ModelChoiceField(
        queryset=Service.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label="Select a Service"
    )
    class Meta:
        model = Booking
        fields = ['service', 'email', 'pet_name', 'pet_type', 'booking_date', 'booking_time', 'notes']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Your Email'}),
            'pet_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Pet Name (optional)'}),
            'pet_type': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Pet Type (optional)'}),
            'booking_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'booking_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Additional notes'}),
        }
        labels = {
            'service': 'Select Service',
            'email': 'Email Address',
            'pet_name': 'Pet Name',
            'pet_type': 'Pet Type',
            'booking_date': 'Booking Date',
            'booking_time': 'Booking Time',
            'notes': 'Additional Notes',
        }