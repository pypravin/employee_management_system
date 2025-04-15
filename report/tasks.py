# tasks.py in the report app
from celery import shared_task
from .models import PerformanceReport
from employee.models import Employee

@shared_task
def generate_monthly_performance_reports():
    employees = Employee.objects.all()  # Get all employees
    for employee in employees:
        PerformanceReport.generate_report(employee)
