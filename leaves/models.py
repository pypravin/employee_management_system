from django.db import models
from django.conf import settings  # Import settings for AUTH_USER_MODEL

class Leave(models.Model):
    LEAVE_TYPES = [
        ('Annual', 'Annual Leave'),
        ('Sick', 'Sick Leave'),
        ('Unpaid', 'Unpaid Leave'),
        ('Maternity', 'Maternity Leave'),
        ('Paternity', 'Paternity Leave'),
        ('Other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Cancelled', 'Cancelled'),  # Add a Cancelled status
    ]

    employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="leaves") # Use AUTH_USER_MODEL
    leave_type = models.CharField(max_length=20, choices=LEAVE_TYPES)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField(blank=True, null=True, default="")  # Optional reason, empty string by default
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_leave_requests') # Add approver and related_name
    approval_date = models.DateTimeField(null=True, blank=True) # Add approval date

    def __str__(self):
        return f"{self.employee.first_name} {self.employee.last_name} - {self.leave_type} ({self.status})"


    class Meta:
        ordering = ['-applied_at']
        verbose_name = "Leave Request"

    def duration(self):
        """Returns the duration of the leave in days."""
        return (self.end_date - self.start_date).days + 1  # +1 to include both start and end dates