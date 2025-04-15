from django.db import models
from employee.models import Employee

class EmployeeReport(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    date_generated = models.DateTimeField(auto_now_add=True)
    leave_balance = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # Total leave balance
    department = models.CharField(max_length=100)
    designation = models.CharField(max_length=100)

    def __str__(self):
        return f"Employee Report for {self.employee.first_name} {self.employee.last_name} on {self.date_generated}"

    @classmethod
    def generate_report(cls, employee):
        # Use the `total_leave_balance` property from the Employee model
        report = cls(
            employee=employee,
            leave_balance=employee.total_leave_balance,
            department=employee.department.name,  # Use the department name
            designation=employee.designation  # Use the employee's designation
        )
        report.save()
        return report

from django.db import models
from attendance.models import Attendance

class AttendanceReport(models.Model):
    attendance = models.ForeignKey(Attendance, on_delete=models.CASCADE)
    date_generated = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20)  # "On Time", "Late", etc.
    time_in = models.TimeField(null=True)
    time_out = models.TimeField(null=True)
    method = models.CharField(max_length=10)  # "Manual" or "Facial"

    def __str__(self):
        return f"Attendance Report for {self.attendance.employee.first_name} on {self.attendance.date}"

    @classmethod
    def generate_report(cls, attendance):
        report = cls(
            attendance=attendance,
            status=attendance.status,
            time_in=attendance.time_in,
            time_out=attendance.time_out,
            method=attendance.method
        )
        report.save()
        return report



from django.db import models
from department.models import Department

class DepartmentReport(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    date_generated = models.DateTimeField(auto_now_add=True)
    department_name = models.CharField(max_length=100)
    active_employees_count = models.IntegerField()

    def __str__(self):
        return f"Department Report for {self.department.name} on {self.date_generated}"

    @classmethod
    def generate_report(cls, department):
        # Count active employees in the department
        active_employees = department.employee_set.filter(is_active=True).count()
        report = cls(
            department=department,
            department_name=department.name,
            active_employees_count=active_employees
        )
        report.save()
        return report

from django.db import models
from attendance.models import Attendance

class LateComerReport(models.Model):
    employee = models.ForeignKey('employee.Employee', on_delete=models.CASCADE)
    date_generated = models.DateTimeField(auto_now_add=True)
    late_time = models.TimeField()
    date = models.DateField()

    def __str__(self):
        return f"Late Comer Report for {self.employee.first_name} on {self.date}"

    @classmethod
    def generate_report(cls, attendance):
        # Ensure that `attendance.is_late()` method exists and returns a boolean
        if attendance.is_late():
            report = cls(
                employee=attendance.employee,
                late_time=attendance.time_in,
                date=attendance.date
            )
            report.save()
            return report

from django.db import models
from employee.models import Employee

class PerformanceReport(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    date_generated = models.DateTimeField(auto_now_add=True)
    attendance_score = models.DecimalField(max_digits=5, decimal_places=2)
    leave_balance = models.DecimalField(max_digits=5, decimal_places=2)
    performance_rating = models.CharField(max_length=50)

    def __str__(self):
        return f"Performance Report for {self.employee.first_name} on {self.date_generated}"

    @classmethod
    def generate_report(cls, employee):
        # Calculate attendance score (assumes Attendance model has `status` field with values like "On Time")
        attendance_score = employee.attendance_set.filter(status="On Time").count()

        # Determine performance rating based on attendance score
        if attendance_score >= 20:
            performance_rating = "Good"
        elif attendance_score >= 10:
            performance_rating = "Average"
        else:
            performance_rating = "Needs Improvement"

        # Create the report
        report = cls(
            employee=employee,
            attendance_score=attendance_score,
            leave_balance=employee.total_leave_balance,  # Use the `total_leave_balance` property
            performance_rating=performance_rating
        )
        report.save()
        return report