from django.shortcuts import render, get_object_or_404
from django.db.models import Count, Q
from django.http import HttpResponse
from django.core.paginator import Paginator
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
import csv
from django.contrib.auth.decorators import login_required
from collections import defaultdict
from employee.models import Employee, Department
from attendance.models import Attendance
from leaves.models import Leave
from .models import EmployeeReport, AttendanceReport, DepartmentReport, LateComerReport, PerformanceReport
import datetime
from datetime import time, timedelta
from django.core.serializers.json import DjangoJSONEncoder
import json
from datetime import timedelta, date
from django.db.models import Count
from django.shortcuts import render
from employee.models import Employee
from attendance.models import Attendance
from department.models import Department
from leaves.models import Leave
from django.shortcuts import render
from .models import Employee
import json
from department.models import Department


@login_required
def report_dashboard(request):
    # Today's date
    today = date.today()
    
    # Basic counts
    total_employees = Employee.objects.filter(is_active=True).count()
    total_departments = Department.objects.filter(is_active=True).count()
    total_attendance = Attendance.objects.filter(date=today).count()
    
    # Late comers (after 9:00 AM)
    late_threshold = time(9, 0)
    late_comers = Attendance.objects.filter(date=today, time_in__gt=late_threshold).count()
    
    # Performance data
    performance_data = Employee.objects.filter(is_active=True)
    performance_names = [f"{emp.first_name} {emp.last_name}" for emp in performance_data]
    performance_scores = [float(emp.calculate_performance()) for emp in performance_data]
    
    # Attendance chart data (last 7 days)
    attendance_data = (
        Attendance.objects
        .filter(date__gte=today - timedelta(days=7))
        .values('date')
        .annotate(total_attendance=Count('id'))
        .order_by('date')
    )
    
    # Prepare clean date strings for chart
    attendance_dates = [record['date'].strftime('%b %d') for record in attendance_data]  # Format as "Jan 01"
    attendance_counts = [record['total_attendance'] for record in attendance_data]
    
    # Context data
    context = {
        # Summary counts
        'total_employees': total_employees,
        'total_departments': total_departments,
        'total_attendance': total_attendance,
        'total_late_comers': late_comers,
        'total_performance': len(performance_data),
        'total_pending_leaves': Leave.objects.filter(status='Pending').count(),
        
        # Chart data (as lists)
        'attendance_dates': attendance_dates,
        'attendance_data': attendance_counts,
        'performance_names': performance_names,
        'performance_scores': performance_scores,
        
        # JSON data for JavaScript
        'attendance_dates_json': json.dumps(attendance_dates, cls=DjangoJSONEncoder),
        'attendance_data_json': json.dumps(attendance_counts),
        'performance_names_json': json.dumps(performance_names),
        'performance_scores_json': json.dumps(performance_scores),
    }
    
    return render(request, 'report/report_dashboard.html', context)



@login_required
def employee_report(request):
    # Get today's date
    today = datetime.date.today()

    # Fetch all active employees
    employees = Employee.objects.filter(is_active=True)

    # Filter by department if selected
    department_id = request.GET.get('department')
    if department_id:
        employees = employees.filter(department_id=department_id)

    # Initialize start_date and end_date with None as default
    start_date = None
    end_date = None

    # Handle date range filtering
    date_range = request.GET.get('date_range')
    if date_range:
        try:
            # Split the date range into start_date and end_date
            start_date, end_date = date_range.split(' to ')
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

            # Filter employees based on attendance within the date range
            if start_date and end_date:
                employees = employees.filter(attendance__date__range=[start_date, end_date])
        except ValueError:
            pass  # Handle invalid date range format

    # Add attendance status to each employee
    for employee in employees:
        # Get the attendance record for each employee for the selected date range
        if start_date and end_date:
            attendance = Attendance.objects.filter(employee=employee, date__range=[start_date, end_date]).first()
        else:
            attendance = Attendance.objects.filter(employee=employee).first()

        if attendance:
            employee.attendance_status = attendance.status
        else:
            employee.attendance_status = 'Absent'

    # Pagination logic
    paginator = Paginator(employees, 10)  # Show 10 employees per page
    page_number = request.GET.get('page')
    employees_page = paginator.get_page(page_number)

    # Fetch all departments to show in the filter
    departments = Department.objects.all()

    context = {
        'employees': employees_page,
        'departments': departments,  # Pass departments to the template
        'date_range': date_range  # Pass the date range back to the template
    }
    return render(request, 'report/employee_report.html', context)



@login_required
def employee_report_export(request, format='csv'):
    # Get all active employees (or filter as needed)
    employees = Employee.objects.filter(is_active=True)

    if format == 'csv':
        # Create the HTTP response with CSV content
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="employee_report.csv"'

        writer = csv.writer(response)
        writer.writerow(['ID', 'Name', 'Email', 'Department'])  # Add your headers here
        for employee in employees:
            writer.writerow([employee.id, f"{employee.first_name} {employee.last_name}", employee.work_email, employee.department.name])  # Add employee data

        return response

    elif format == 'pdf':
        # Create an HTTP response for PDF
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        p.drawString(100, height - 100, "Employee Report")

        # Set the column names
        y_position = height - 120
        p.drawString(100, y_position, "ID")
        p.drawString(200, y_position, "Name")
        p.drawString(300, y_position, "Email")
        p.drawString(400, y_position, "Department")

        # Add the employee details
        for employee in employees:
            y_position -= 20
            p.drawString(100, y_position, str(employee.id))
            p.drawString(200, y_position, f"{employee.first_name} {employee.last_name}")
            p.drawString(300, y_position, employee.work_email)
            p.drawString(400, y_position, employee.department.name)

        p.showPage()
        p.save()

        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="employee_report.pdf"'

        return response



@login_required
def employee_report_detail(request, id):
    # Fetch the employee
    employee = get_object_or_404(Employee, pk=id)

    # Get today's date
    today = datetime.date.today()

    # Fetch today's attendance for the employee
    attendance = Attendance.objects.filter(employee=employee, date=today).first()

    # Debugging: Print attendance record and status
    print(f"Employee: {employee.first_name} {employee.last_name}, Attendance: {attendance}")

    # Set attendance status
    if attendance:
        employee.attendance_status = attendance.status
    else:
        employee.attendance_status = 'Absent'  # Set to Absent if no record for today

    # Pass employee and attendance status to the context
    context = {'employee': employee, 'attendance_status': employee.attendance_status}
    
    return render(request, 'report/employee_report_detail.html', context)




@login_required
def attendance_report(request):
    # Fetch all attendance records
    attendance_records = Attendance.objects.all()
    if not attendance_records.exists():
        attendance_records = None  # Set to None if no attendance records are found

    # Prepare data for the chart
    attendance_labels = []
    attendance_data = []
    
    # Get distinct department names from the Attendance records
    departments = Attendance.objects.values('employee__department__name').distinct()
    
    for department in departments:
        department_name = department['employee__department__name']
        if department_name:  # Ensure department_name is not None
            attendance_labels.append(department_name)
            # Count the number of 'On Time' or 'Late' records for this department
            present_count = Attendance.objects.filter(
                employee__department__name=department_name, 
                status__in=['On Time', 'Late']  # Count both 'On Time' and 'Late' as "Present"
            ).count()
            attendance_data.append(present_count)
    
    # Convert Python lists to JSON strings
    attendance_labels_json = json.dumps(attendance_labels)
    attendance_data_json = json.dumps(attendance_data)
    
    context = {
        'departments': departments,
        'attendance_records': attendance_records,
        'attendance_labels_json': attendance_labels_json,
        'attendance_data_json': attendance_data_json
    }
    
    return render(request, 'report/attendance_report.html', context)

# Department Report View
def department_report(request):
    departments = Department.objects.filter(is_active=True)  # Filter out inactive departments
    if not departments.exists():
        departments = None  # Set to None if no departments are found
    context = {'departments': departments}
    return render(request, 'report/department_report.html', context)

@login_required
def late_comer_report(request):
    # Fetch all attendance records
    attendance_records = Attendance.objects.all()

    # Apply filters if provided
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    employee_name = request.GET.get('employee')

    if start_date:
        start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
        attendance_records = attendance_records.filter(date__gte=start_date)
    
    if end_date:
        end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
        attendance_records = attendance_records.filter(date__lte=end_date)
    
    if employee_name:
        attendance_records = attendance_records.filter(
            employee__first_name__icontains=employee_name
        ) | attendance_records.filter(
            employee__last_name__icontains=employee_name
        )

    # Filter for latecomers using the is_late method
    late_comers = [record for record in attendance_records if record.is_late()]

    # Ensure late_comers is never None
    if not late_comers:
        late_comers = []  # Set to empty list if no latecomers are found
    
    # Prepare data for serialization
    late_comer_data = [
        {
            'employee_id': record.employee.display_employee_id,
            'employee_name': f"{record.employee.first_name} {record.employee.last_name}",
            'date': record.date.strftime('%Y-%m-%d'),  # Format the date
            'time_in': record.time_in.strftime('%I:%M %p') if record.time_in else None,  # Format the time
            'status': record.status
        }
        for record in late_comers
    ]

    # Group data by date for the chart
    from collections import defaultdict
    date_count = defaultdict(int)
    for record in late_comers:
        date_count[record.date.strftime('%Y-%m-%d')] += 1

    # Convert Python data to JSON-serializable format
    late_comer_labels = list(date_count.keys())  # Dates
    late_comer_data_counts = list(date_count.values())  # Count of latecomers per date

    # Convert the lists to JSON
    late_comer_labels_json = json.dumps(late_comer_labels)
    late_comer_data_counts_json = json.dumps(late_comer_data_counts)

    context = {
        'late_comers': late_comer_data,
        'late_comer_labels_json': late_comer_labels_json,
        'late_comer_data_counts_json': late_comer_data_counts_json,
        'departments': Department.objects.all()  # Add departments for the filter dropdown
    }
    
    return render(request, 'report/late_comer_report.html', context)




@login_required
def performance_report(request):
    employees = Employee.objects.filter(is_active=True)  # Get only active employees

    # Apply filters
    department = request.GET.get('department')
    if department and department.isdigit():
        employees = employees.filter(department_id=int(department))

    designation = request.GET.get('designation')
    if designation:
        employees = employees.filter(designation__icontains=designation)  # Case-insensitive search

    employee_search = request.GET.get('employee_search')
    if employee_search:
        employees = employees.filter(first_name__icontains=employee_search) | employees.filter(last_name__icontains=employee_search)

    if not employees.exists():
        employees = Employee.objects.none()  # Ensure queryset remains valid

    performance_data = []
    for employee in employees:
        performance_score = employee.calculate_performance() or 0
        performance_data.append({
            'name': f"{employee.first_name} {employee.last_name}",
            'performance_score': float(performance_score)
        })

    # Prepare data for the chart
    performance_labels = [data['name'] for data in performance_data]
    performance_scores = [data['performance_score'] for data in performance_data]

    context = {
        'employees': employees,
        'performance_data': performance_data,
        'departments': Department.objects.all(),
        'performance_labels': performance_labels,
        'performance_scores': performance_scores
    }
    return render(request, 'report/performance_report.html', context)
