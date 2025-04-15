from django import forms
from .models import Department
import re

class DepartmentForm(forms.ModelForm):
    name = forms.CharField(
        label="Department Name",
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter department name'
        })
    )
    description = forms.CharField(
        label="Department Description",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'maxlength': '500',
            'placeholder': 'Enter department description'
        })
    )

    class Meta:
        model = Department
        fields = ['name', 'description']

    def clean_name(self):
        name = self.cleaned_data.get('name')

        # Allow only letters and spaces (No numbers or special characters)
        if not re.match(r'^[A-Za-z\s]+$', name):
            raise forms.ValidationError("Department name should only contain letters and spaces.")

        return name

    def clean_description(self):
        description = self.cleaned_data.get('description')

        # Optional: Limit excessive special characters (allow basic punctuation)
        if not re.match(r'^[A-Za-z0-9\s.,!?()-]+$', description):
            raise forms.ValidationError("Description contains invalid characters.")

        return description
