from django import forms
from .models import Booking, Service, ServiceCenter


class BookingForm(forms.ModelForm):
    service = forms.ModelChoiceField(
        queryset=Service.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label="Select a Service"
    )

    class Meta:
        model = Booking
        fields = [
            'service', 'service_location', 'service_center', 'home_address', 'contact_number',
            'email', 'pet_name', 'pet_type', 'booking_date', 'booking_time', 'notes'
        ]
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Your Email'}),
            'pet_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Pet Name (optional)'}),
            'pet_type': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Pet Type (optional)'}),
            'booking_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'booking_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Additional notes'}),
            'service_center': forms.Select(attrs={'class': 'form-select'}),
            'home_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Your address'}),
            'contact_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Contact Number'}),
        }
        labels = {
            'service': 'Select Service',
            'service_location': 'Booking Type',
            'service_center': 'Select Service Center',
            'home_address': 'Home Address',
            'contact_number': 'Contact Number',
            'email': 'Email Address',
            'pet_name': 'Pet Name',
            'pet_type': 'Pet Type',
            'booking_date': 'Booking Date',
            'booking_time': 'Booking Time',
            'notes': 'Additional Notes',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Use radio select for service_location
        self.fields['service_location'].widget = forms.RadioSelect(choices=Booking.SERVICE_LOCATION_CHOICES)
        # Service center queryset and optional
        self.fields['service_center'].queryset = ServiceCenter.objects.all()
        self.fields['service_center'].required = False
        # Make home_address and contact_number optional by default
        self.fields['home_address'].required = False
        self.fields['contact_number'].required = False

    def clean(self):
        cleaned_data = super().clean()
        location = cleaned_data.get('service_location')
        center = cleaned_data.get('service_center')
        address = cleaned_data.get('home_address')
        contact = cleaned_data.get('contact_number')

        if location == 'center' and not center:
            self.add_error('service_center', 'Please select a service center.')
        if location == 'home':
            if not address:
                self.add_error('home_address', 'Please provide your home address.')
            if not contact:
                self.add_error('contact_number', 'Please provide a contact number.')
