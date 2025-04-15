from datetime import date
from .models import Leave

def is_employee_on_leave(employee):
    """
    Check if the given employee has an approved leave covering today's date.
    Returns True if the employee is on leave, otherwise False.
    """
    today = date.today()
    return Leave.objects.filter(
        employee=employee,
        status="Approved",
        start_date__lte=today,
        end_date__gte=today
    ).exists()
