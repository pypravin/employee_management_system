from django import forms
from .models import Leave
from django.utils import timezone

class LeaveRequestForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)  # Get the user from kwargs
        super().__init__(*args, **kwargs)
        today = timezone.now().date()
        self.fields['start_date'].widget.attrs['min'] = today.isoformat()
        self.fields['end_date'].widget.attrs['min'] = today.isoformat()

    class Meta:
        model = Leave
        fields = ['leave_type', 'start_date', 'end_date', 'reason']
        widgets = {
            'leave_type': forms.Select(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        print(f"Start Date from Form: {start_date}")
        print(f"Today's Date (Server Time): {timezone.now().date()}")

        if not self.user:
            raise forms.ValidationError("User must be authenticated to request leave.")

        if start_date and end_date:
            if start_date > end_date:
                raise forms.ValidationError("End date cannot be before start date.")
            if start_date < timezone.now().date():
                raise forms.ValidationError("Start date cannot be in the past.")
            if end_date < timezone.now().date():
                raise forms.ValidationError("End date cannot be in the past.")

            # Check for overlapping leave requests
            employee = self.instance.employee if self.instance.pk else self.user

            existing_leaves = Leave.objects.filter(
                employee=employee,
                start_date__lte=end_date,
                end_date__gte=start_date,
                status__in=['Pending', 'Approved']
            ).exclude(pk=self.instance.pk if self.instance.pk else None)

            if existing_leaves.exists():
                raise forms.ValidationError("You already have a leave request for these dates.")

        return cleaned_data