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
        initial=datetime.date.today
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

    class Meta:
        model = Attendance
        fields = ["employee", "date", "time_in", "time_out"]

    def clean_date(self):
        selected_date = self.cleaned_data.get("date")
        today = now().date()

        if selected_date > today:
            raise forms.ValidationError("You cannot select a future date.")
        # Optional: Block past entries too
        # if selected_date < today:
        #     raise forms.ValidationError("You cannot select a past date.")
        return selected_date

    def clean(self):
        cleaned_data = super().clean()
        employee = cleaned_data.get("employee")
        date = cleaned_data.get("date")
        time_in = cleaned_data.get("time_in")
        time_out = cleaned_data.get("time_out")

        if time_out and not time_in:
            raise forms.ValidationError("Cannot set Time Out without Time In.")

        if time_in and time_out and time_out <= time_in:
            raise forms.ValidationError("Time Out cannot be before or equal to Time In.")

        if employee and date:
            existing = Attendance.objects.filter(employee=employee, date=date)
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise forms.ValidationError("Attendance already recorded for this employee on this date.")

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.method = "Manual"
        if commit:
            instance.save()
        return instance
