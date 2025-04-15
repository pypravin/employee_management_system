import datetime
from django import forms
from .models import Attendance
from employee.models import Employee
from django.forms import TimeInput, DateInput
from django.utils.timezone import now

class ManualAttendanceForm(forms.ModelForm):
    employee = forms.ModelChoiceField(
        queryset=Employee.objects.filter(is_active=True),
        label="Select Employee",
        widget=forms.Select(attrs={"class": "form-control"})
    )
    date = forms.DateField(
        label="Date",
        widget=DateInput(attrs={"class": "form-control", "type": "date"}),
        initial=datetime.date.today  # Set initial date to today
    )
    time_in = forms.TimeField(
        label="Time In",
        widget=TimeInput(attrs={"class": "form-control", "type": "time"}),
        required=False
    )
    time_out = forms.TimeField(
        label="Time Out",
        widget=TimeInput(attrs={"class": "form-control", "type": "time"}),
        required=False
    )
    status = forms.CharField(
        label="Status",
        widget=forms.TextInput(attrs={"class": "form-control"}),
        required=False
    )

    class Meta:
        model = Attendance
        fields = ["employee", "date", "time_in", "time_out", "status"]

    def clean_date(self):
        """Prevent future dates in attendance selection"""
        selected_date = self.cleaned_data.get("date")
        today = now().date()

        if selected_date > today:
            raise forms.ValidationError("You cannot select a future date.")

        return selected_date

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.method = "Manual"
        if commit:
            instance.save()
        return instance
