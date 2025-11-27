from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User
from .models import Equipment, Supplier
from .models import EquipmentRequest

class EquipmentRequestForm(forms.ModelForm):
    class Meta:
        model = EquipmentRequest
        fields = ['equipment', 'quantity', 'purpose']

class RegisterForm(UserCreationForm):
    ROLE_CHOICES = [
        ('Admin', 'Admin'),
        ('Staff', 'Staff'),
        ('Viewer', 'Viewer'),
    ]
    role = forms.ChoiceField(choices=ROLE_CHOICES, required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'role', 'password1', 'password2']

class EquipmentForm(forms.ModelForm):
    class Meta:
        model = Equipment
        fields = [
            'name',
            'category',
            'quantity',
            'location',
            'condition',
            'description',
            'datasheet',
            'image'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Equipment Name'}),
            'category': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Category'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Quantity'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Location'}),
            'condition': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Condition'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Short description', 'rows': 4}),
            'datasheet': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Datasheet URL'}),
        }

class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['name', 'equipments_available','contact_no', 'email', 'street', 'city', 'pincode']
