from django.db import models
from employee.models import Employee
import datetime


class Attendance(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    # Date field for attendance
    date = models.DateField(default=datetime.date.today)
    # Time when the employee clocks in
    time_in = models.TimeField(null=True, blank=True)
    # Time when the employee clocks out
    time_out = models.TimeField(null=True, blank=True)
    method = models.CharField(max_length=10, choices=[(
        "Manual", "Manual"), ("Facial", "Facial")])  # Attendance method
    # Status: e.g., "On Time", "Late"
    status = models.CharField(max_length=20, null=True,
                              blank=True, default="Absent")
    # Timestamp for when the record was created
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Prevent duplicate attendance records for the same day
        unique_together = ('employee', 'date')

    def __str__(self):
        return f"Attendance for {self.employee.display_employee_id} on {self.date}"

    def is_late(self):
        expected_time = datetime.time(9, 0, 0)  # 9:00 AM
        return bool(self.time_in and self.time_in > expected_time)

    def is_early_departure(self):
        """ Check if the time_out is before the expected time (e.g., 5:00 PM). """
        expected_time = datetime.time(17, 0, 0)  # 5:00 PM
        return self.time_out and self.time_out < expected_time

    def save(self, *args, **kwargs):
        """ Override save to set attendance status based on time_in and time_out. """
        if self.time_in:
            self.status = "Late" if self.is_late() else "On Time"
        if self.time_out:
            if self.is_early_departure():
                self.status = "Early Departure"
            elif self.status != "Late":  # Only set "On Time" if not late already
                self.status = "On Time"
        super().save(*args, **kwargs)
