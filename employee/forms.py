from django import forms
from django.utils import timezone
from .models import Employee, Department
import re

class EmployeeForm(forms.ModelForm):
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        empty_label="Select Department",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Employee
        fields = [
            'first_name', 'last_name', 'department', 'designation', 
            'hire_date', 'work_email', 'annual_leave_balance', 'sick_leave_balance'
        ]
        widgets = {
            'hire_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'designation': forms.TextInput(attrs={'class': 'form-control'}),
            'work_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'annual_leave_balance': forms.NumberInput(attrs={'class': 'form-control'}),
            'sick_leave_balance': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def clean_first_name(self):
        first_name = self.cleaned_data.get("first_name")
        if any(char.isdigit() for char in first_name):
            raise forms.ValidationError("First name should not contain numbers.")
        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get("last_name")
        if any(char.isdigit() for char in last_name):
            raise forms.ValidationError("Last name should not contain numbers.")
        return last_name

    def clean_designation(self):
        designation = self.cleaned_data.get("designation")
        if not designation:
            raise forms.ValidationError("Designation is required.")
        if re.search(r"[^a-zA-Z\s]", designation):  # Allows only letters and spaces
            raise forms.ValidationError("Designation should not contain numbers or special characters.")
        return designation

    def clean_work_email(self):
        work_email = self.cleaned_data.get("work_email")

        if not work_email:
            raise forms.ValidationError("Work email is required.")

        work_email = work_email.strip().lower()

        allowed_domains = ["yourcompany.com", "anotheralloweddomain.net","gmail.com","hotmail.com"]  # Update this list

        domain = work_email.split("@")[-1]

        if domain not in allowed_domains:
            raise forms.ValidationError(
                "Work email must be a valid company email (e.g., user@yourcompany.com)."
            )

        return work_email

    def clean_hire_date(self):
        hire_date = self.cleaned_data.get("hire_date")
        today = timezone.now().date()
        if hire_date and hire_date < today:
            raise forms.ValidationError("Hire date cannot be in the past.")
        return hire_date

    def clean_annual_leave_balance(self):
        leave_balance = self.cleaned_data.get("annual_leave_balance") or 0
        if leave_balance < 0:
            raise forms.ValidationError("Annual leave balance cannot be negative.")
        return leave_balance

    def clean_sick_leave_balance(self):
        sick_balance = self.cleaned_data.get("sick_leave_balance") or 0
        if sick_balance < 0:
            raise forms.ValidationError("Sick leave balance cannot be negative.")
        return sick_balance
