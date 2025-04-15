from django.db import models
from django.conf import settings  # Use settings.AUTH_USER_MODEL instead of User
from employee.models import Employee, Department  # Import Employee and Department
from django.urls import reverse

class Notification(models.Model):
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_urgent = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True)

    # 🔹 Links to Event or Announcement (Only one should be set)
    event = models.ForeignKey("Event", on_delete=models.CASCADE, null=True, blank=True)
    announcement = models.ForeignKey("Announcement", on_delete=models.CASCADE, null=True, blank=True)

    recipients = models.ManyToManyField(Employee, related_name="notifications", blank=True)
    departments = models.ManyToManyField(Department, related_name="notifications", blank=True)

    def __str__(self):
        return self.title

    def get_redirect_url(self):
        """ Returns the appropriate URL for this notification. """
        if self.event:
            return reverse("view_event", kwargs={"event_id": self.event.id})
        elif self.announcement:
            return reverse("view_announcement", kwargs={"announcement_id": self.announcement.id})
        return "#"  # Default (no action)

class Event(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    event_date = models.DateTimeField()
    location = models.CharField(max_length=255, blank=True, null=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="events_created"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)  # Soft delete

    # NEW: Allow HR to select employees and departments
    attendees = models.ManyToManyField(Employee, related_name="events_attended", blank=True)
    departments = models.ManyToManyField(Department, related_name="events", blank=True)

    select_all_employees = models.BooleanField(default=False)  # Add this field
    select_all_departments = models.BooleanField(default=False)  # Add t

    def __str__(self):
        return self.title


class EventRegistration(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    registered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('event', 'employee')  # Prevent duplicate registrations

    def __str__(self):
        return f"{self.employee.full_name} - {self.event.title}"



class NotificationRecipient(models.Model):
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE)
    recipient = models.ForeignKey(Employee, on_delete=models.CASCADE)  # Changed this line
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.recipient.full_name} - {self.notification.title}"


class Announcement(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.title
