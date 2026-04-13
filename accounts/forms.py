from django import forms
from .models import SellerApplication


class SellerApplicationForm(forms.ModelForm):
    class Meta:
        model = SellerApplication
        fields = [
            'shop_name',
            'phone',
            'address',
            'business_type',
            'gst_number',
            'description',
        ]

        widgets = {
            'shop_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter shop name'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter phone number'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter full address'
            }),
            'business_type': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Electronics, Fashion'
            }),
            'gst_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter GST number (optional)'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Tell about your shop/business'
            }),
        }

    # 🔥 Validation (important)
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')

        if not phone.isdigit():
            raise forms.ValidationError("Phone number must contain only digits.")

        if len(phone) < 10:
            raise forms.ValidationError("Phone number must be at least 10 digits.")

        return phone