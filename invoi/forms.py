from django import forms
from .models import Invoice

class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = [
            'bill_to', 'email', 'address', 'place', 'phone', 'date',
            'description', 'quantity', 'unit_price'
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 2}),
        }
