from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
import re
from .models import Notification, Event, Announcement
from employee.models import Employee
from department.models import Department


# Utility function for validation
def no_special_characters(value):
    print(f"Inside no_special_characters with value: '{value}'")
    if not re.match(r'^[a-zA-Z0-9\s]*$', value):
        print("Validation failed (special characters) in no_special_characters")
        raise ValidationError("This field cannot contain special characters.")
    elif value.isdigit():
        print("Validation failed (only digits) in no_special_characters")
        raise ValidationError("This field cannot contain only numeric values.")
    else:
        print("Validation passed in no_special_characters")
    return value


class NotificationForm(forms.ModelForm):
    recipients = forms.ModelMultipleChoiceField(
        queryset=Employee.objects.filter(is_active=True),
        widget=forms.SelectMultiple(attrs={'class': 'select2'}),
        required=False,
        help_text="Select employees to notify"
    )

    departments = forms.ModelMultipleChoiceField(
        queryset=Department.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'select2'}),
        required=False,
        help_text="Select departments to notify"
    )

    class Meta:
        model = Notification
        fields = ['title', 'message', 'is_urgent', 'recipients', 'departments']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter notification title'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Enter message', 'rows': 3}),
            'is_urgent': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_title(self):
        title = self.cleaned_data['title']
        no_special_characters(title)
        return title

    def clean_message(self):
        message = self.cleaned_data['message']
        # Optionally, you can add validation for the message field here.
        return message


class EventForm(forms.ModelForm):
    attendees = forms.ModelMultipleChoiceField(
        queryset=Employee.objects.filter(is_active=True),
        widget=forms.SelectMultiple(attrs={'class': 'select2'}),
        required=False,
        help_text="Select employees to invite"
    )

    departments = forms.ModelMultipleChoiceField(
        queryset=Department.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'select2'}),
        required=False,
        help_text="Select departments to invite"
    )

    # Add checkboxes for Select All functionality
    select_all_employees = forms.BooleanField(required=False, initial=False)
    select_all_departments = forms.BooleanField(required=False, initial=False)

    class Meta:
        model = Event
        fields = ['title', 'description', 'event_date', 'location', 'attendees', 'departments', 'select_all_employees', 'select_all_departments']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter event title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Enter event details', 'rows': 3}),
            'event_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter event location'}),
        }

    def clean_title(self):
        title = self.cleaned_data['title']
        print(f"Inside clean_title with title: '{title}'") # ADDED
        no_special_characters(title)
        return title

    def clean_description(self):
        description = self.cleaned_data['description']
        print(f"Inside clean_description with description: '{description}'")
        if description.isdigit():
            print("Validation failed (only digits) in clean_description")
            raise ValidationError("This field cannot contain only numeric values.")
        return description

    def clean_location(self):
        location = self.cleaned_data['location']
        print(f"Inside clean_location with location: '{location}'") # ADDED
        no_special_characters(location)
        return location

    def clean_event_date(self):
        event_date = self.cleaned_data['event_date']
        now = timezone.now()
        one_month_future = now + timedelta(days=30)

        if event_date < now:
            raise ValidationError("Event date cannot be in the past.")
        if event_date > one_month_future:
            raise ValidationError("Event date cannot be more than one month in the future.")
        return event_date