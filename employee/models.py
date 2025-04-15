from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
import uuid
import random
import string
from django.contrib.auth.hashers import make_password
from department.models import Department
from django.core.validators import RegexValidator
from decimal import Decimal
import datetime


# Custom Manager for Employee
class EmployeeManager(BaseUserManager):
    def get_queryset(self):
        """Exclude soft-deleted employees from queries by default."""
        return super().get_queryset().filter(is_deleted=False)

    def create_user(self, first_name, last_name, work_email, department, designation, password=None):
        if not work_email:
            raise ValueError("Employees must have a valid email address")

        department_instance = Department.objects.get(id=department)

        user = self.model(
            first_name=first_name,
            last_name=last_name,
            work_email=self.normalize_email(work_email),
            department=department_instance,
            designation=designation,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, first_name, last_name, work_email, department, designation, password=None):
        user = self.create_user(
            first_name=first_name,
            last_name=last_name,
            work_email=work_email,
            department=department,
            designation=designation,
            password=password,
        )
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class Employee(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    display_employee_id = models.CharField(max_length=10, unique=True, editable=False, null=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, db_column="department_id", db_constraint=False)
    designation = models.CharField(max_length=50)
    hire_date = models.DateField(null=True, blank=True)
    work_email = models.EmailField(unique=True)

    phone_validator = RegexValidator(
        regex=r'^9\d{9}$', 
        message="Phone number must be exactly 10 digits and start with 9."
    )
    phone_number = models.CharField(max_length=10, blank=True, null=True, validators=[phone_validator])
    emergency_contact = models.CharField(max_length=10, blank=True, null=True, validators=[phone_validator])

    annual_leave_balance = models.DecimalField(max_digits=5, decimal_places=2, default=20)
    sick_leave_balance = models.DecimalField(max_digits=5, decimal_places=2, default=20)
    performance_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)

    facial_enrollment_status = models.BooleanField(default=False)
    face_model_path = models.CharField(max_length=255, blank=True, null=True)
    first_login = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)  # Soft delete flag
    is_hr = models.BooleanField(default=False)  
    is_staff = models.BooleanField(default=False)  
    is_superuser = models.BooleanField(default=False)  

    objects = EmployeeManager()

    USERNAME_FIELD = "work_email"
    REQUIRED_FIELDS = ["first_name", "last_name", "department", "designation"]

    class Meta:
        verbose_name = "Employee"
        verbose_name_plural = "Employees"

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.work_email})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def total_leave_balance(self):
        return (self.annual_leave_balance or 0) + (self.sick_leave_balance or 0)

    def save(self, *args, **kwargs):
        """Generate Employee ID if not set"""
        if not self.display_employee_id:
            self.display_employee_id = self.generate_display_employee_id()
        super().save(*args, **kwargs)

    @staticmethod
    def generate_display_employee_id():
        """Generate a unique employee ID"""
        while True:
            display_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            if not Employee.objects.filter(display_employee_id=display_id).exists():
                return display_id
    
    def calculate_leave_balance(self, leave_type):
        if leave_type == 'Annual':
            return self.annual_leave_balance
        elif leave_type == 'Sick':
            return self.sick_leave_balance
        return 0.0

    def update_leave_balance(self, leave_type, days, action='deduct'):
        balance_field = f"{leave_type.lower()}_leave_balance"
        if hasattr(self, balance_field):
            current_balance = getattr(self, balance_field)
            if action == 'deduct':
                if current_balance >= days:  # Add this check
                    setattr(self, balance_field, current_balance - days)
                else:
                    raise ValueError(f"Insufficient {leave_type} leave balance.") # Or handle this as needed
            elif action == 'add':
                setattr(self, balance_field, current_balance + days)
            self.save(update_fields=[balance_field])

    
    def calculate_performance(self):
        # Start with a base score of 100 as Decimal
        performance_score = Decimal('100.0')


        # Penalize for leave balance over a certain threshold
        if self.total_leave_balance < Decimal('10.0'):
            performance_score -= Decimal('10.0')  # Penalize for poor leave balance management

        # Penalize for absence - if no attendance records are found for the current month
        attendance_rate = self.get_attendance_rate()  # Fetch actual attendance rate
        if attendance_rate < 80.0:  # Below 80% attendance penalizes the score
            performance_score -= Decimal('10.0')
        

        # Penalize employees with late arrivals (2 points per late arrival)
        late_arrivals = self.get_late_arrivals_count()  # Fetch actual late arrivals count
        late_arrival_penalty = Decimal(str(late_arrivals)) * Decimal('2.0')
        performance_score -= late_arrival_penalty
       

        # Performance boost based on attendance rate
        if attendance_rate >= 90.0:
            performance_score += Decimal('5.0')  # Full boost for excellent attendance
        elif attendance_rate >= 80.0:
            performance_score += Decimal('2.0')  # Partial boost for good attendance
        

        # Ensure the score is between 0 and 100
        performance_score = max(Decimal('0.0'), min(Decimal('100.0'), performance_score))
        
        return performance_score




    def get_late_arrivals_count(self):
        """
        Get the number of late arrivals for this employee.
        """
        from attendance.models import Attendance  # Lazy import to avoid circular dependency
        late_arrivals_count = Attendance.objects.filter(employee=self, status="Late").count()
        print(f"Late Arrivals Count for {self.full_name}: {late_arrivals_count}")
        return late_arrivals_count



    def get_attendance_rate(self):
        """
        Get the attendance rate for this employee.
        """
        from attendance.models import Attendance  # Lazy import to avoid circular dependency
        current_month = datetime.datetime.now().month
        total_days = Attendance.objects.filter(employee=self, date__month=current_month).count()
        present_days = Attendance.objects.filter(employee=self, date__month=current_month, status="On Time").count()
        
        print(f"Attendance Rate for {self.full_name} - Total Days: {total_days}, Present Days: {present_days}")
        
        if total_days > 0:
            return (present_days / total_days) * 100  # Return attendance rate as a float
        return 0.0  # Return 0.0 if no records are found

    def save(self, *args, **kwargs):
        """Generate Employee ID if not set and calculate performance score"""
        if not self.display_employee_id:
            self.display_employee_id = self.generate_display_employee_id()

        # Calculate and update performance score
        self.performance_score = self.calculate_performance()

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Soft delete - Mark employee as inactive instead of deleting."""
        self.is_deleted = True
        self.is_active = False
        self.save(update_fields=["is_deleted", "is_active"])

    def restore(self):
        """Restore a soft-deleted employee"""
        self.is_deleted = False
        self.is_active = True
        self.save(update_fields=["is_deleted", "is_active"])