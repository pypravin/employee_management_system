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

        today = timezone.now().date()

        if not self.user:
            raise forms.ValidationError("User must be authenticated to request leave.")

        if start_date and end_date:
            # 1. Check start_date is not in the past
            if start_date < today:
                raise forms.ValidationError("Start date cannot be in the past.")

            # 2. Check end_date is not before start_date
            if end_date < start_date:
                raise forms.ValidationError("End date cannot be before start date.")

            # 3. Check start_date is not more than 7 days in the future
            if (start_date - today).days > 7:
                raise forms.ValidationError("Start date cannot be more than 7 days in the future.")

            # 4. Check duration does not exceed 7 days
            duration = (end_date - start_date).days + 1
            if duration > 7:
                raise forms.ValidationError("Leave duration cannot exceed 7 days.")

            # 5. Check start_date and end_date are not Saturdays
            if start_date.weekday() == 5:  # 5 = Saturday
                raise forms.ValidationError("Start date cannot be a Saturday.")
            if end_date.weekday() == 5:
                raise forms.ValidationError("End date cannot be a Saturday.")

            # 6. Check for overlapping leaves
            employee = self.instance.employee if self.instance.pk else self.user

            overlapping_leaves = Leave.objects.filter(
                employee=employee,
                start_date__lte=end_date,
                end_date__gte=start_date,
                status__in=['Pending', 'Approved']
            ).exclude(pk=self.instance.pk if self.instance.pk else None)

            if overlapping_leaves.exists():
                raise forms.ValidationError("You already have an existing leave that overlaps with these dates.")

        return cleaned_data
