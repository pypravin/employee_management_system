from django.shortcuts import render, redirect, get_object_or_404
from employee.models import Employee
from employee.forms import EmployeeForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.timezone import now
from attendance.models import Attendance
from leaves.models import Leave
from department.models import Department
from django.utils import timezone
from django.db.models import Count
from collections import defaultdict
import json





def custom_404(request, exception):
    return render(request, '404.html', status=404)

def custom_500(request):
    return render(request, '500.html', status=500)

def custom_403(request, exception):
    return render(request, '403.html', status=403)



def universal_login(request):
    if request.user.is_authenticated:
        
        pass # For now, just do nothing if authenticated on GET request

    if request.method == "POST":
        email = request.POST['username']  # Use 'username' for consistency
        password = request.POST['password']
        user = authenticate(request, username=email, password=password)  # Use 'username' for authentication

        if user is not None:
            login(request, user)
            return redirect_user_based_on_role(user)
        else:
            messages.error(request, "Invalid credentials. Please try again.")

    return render(request, 'universal_login.html')

def redirect_user_based_on_role(user):
    """Redirect users based on their role"""
    if user.is_superuser:
        return redirect('admin:index')  # Redirect superusers to Django admin
    elif user.is_hr:
        return redirect('hr_portal:hr_dashboard')  # Redirect HR users to HR portal
    else:
        return redirect('employee_portal:employee_dashboard')

def universal_logout(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect('employee_portal:universal_login')


@login_required
@user_passes_test(lambda u: u.is_hr or u.is_superuser)
def hr_dashboard(request):
    today = timezone.now().date()

    # 1. Total Number of Employees
    total_employees = Employee.objects.filter(is_active=True, is_deleted=False).count()

    # 2. Number of Employees Attended Today
    attended_today_count = Attendance.objects.filter(date=today).values('employee').distinct().count()

    # 3. Number of Employees on Leave Today
    on_leave_today_count = Leave.objects.filter(
        status='Approved',
        start_date__lte=today,
        end_date__gte=today
    ).values('employee').distinct().count()

    # 4. Number of Employees Absent Today
    absent_today_count = total_employees - attended_today_count - on_leave_today_count

    # **New: Count of Pending Leave Requests**
    pending_leave_count = Leave.objects.filter(status='Pending').count()

    # Prepare summary data for the cards
    summary_data = [
        {'title': 'Total Employees', 'count': total_employees, 'label': '', 'icon': 'bi bi-people', 'color': 'primary', 'view_url': 'employee:employee_list'},
        {'title': 'Attendance Today', 'count': attended_today_count, 'label': '', 'icon': 'bi bi-check-circle-fill', 'color': 'success', 'view_url': 'attendance:attendance_list'},
        {'title': 'Absent Today', 'count': absent_today_count, 'label': '', 'icon': 'bi bi-x-circle-fill', 'color': 'danger', 'view_url': 'attendance:absent_list'},
        {'title': 'On Leave Today', 'count': on_leave_today_count, 'label': '', 'icon': 'bi bi-sun-fill', 'color': 'warning', 'view_url': 'hr_portal:hr_leave_list'},
        # **Optional: Add a card for pending leaves**
        {'title': 'Pending Leaves', 'count': pending_leave_count, 'label': 'Requests', 'icon': 'bi bi-hourglass-split', 'color': 'info', 'view_url': 'hr_portal:hr_leave_list'},
    ]

    # 5. Data for Attendance by Department Chart
    department_attendance = Attendance.objects.filter(date=today).values('employee__department__name').annotate(present_count=Count('employee'))
    total_employees_by_department = Employee.objects.filter(is_active=True, is_deleted=False).values('department__name').annotate(total_count=Count('id'))

    department_attendance_data_map = {item['employee__department__name']: item['present_count'] for item in department_attendance}
    total_employees_map = {item['department__name']: item['total_count'] for item in total_employees_by_department}

    department_names = list(total_employees_map.keys())
    department_attendance_percentages = []

    for dept_name in department_names:
        present = department_attendance_data_map.get(dept_name, 0)
        total = total_employees_map.get(dept_name, 1) # Avoid division by zero
        percentage = (present / total) * 100 if total > 0 else 0
        department_attendance_percentages.append(round(percentage, 2))

    # 6. Data for Performance Overview Chart
    performance_data = [0, 0, 0, 0]  # [Excellent, Good, Average, Poor]
    for employee in Employee.objects.filter(is_active=True, is_deleted=False):
        score = employee.performance_score  # Assuming calculate_performance() updates this field
        if score >= 90:
            performance_data[0] += 1
        elif score >= 70:
            performance_data[1] += 1
        elif score >= 50:
            performance_data[2] += 1
        else:
            performance_data[3] += 1

    context = {
        'summary_data': summary_data,
        'department_names': json.dumps(department_names),
        'department_attendance_data': json.dumps(department_attendance_percentages),
        'performance_data': json.dumps(performance_data),
        'pending_leave_count': pending_leave_count, # Pass the count to the template
    }
    return render(request, 'hr_portal/hr_dashboard.html', context)


@login_required
@user_passes_test(lambda u: u.is_hr or u.is_superuser)  
def register_employee(request):
    if request.method == "POST":
        form = EmployeeForm(request.POST)
        if form.is_valid():
            employee = form.save()
            return redirect('employee_detail', employee_id=employee.id)  # Redirect to details page
    else:
        form = EmployeeForm()
    
    return render(request, 'hr_portal/register_employee.html', {'form': form})



@login_required
@user_passes_test(lambda u: u.is_hr or u.is_superuser)
def hr_leave_list(request):
    leaves = Leave.objects.all().order_by('-applied_at')  # HR sees all leaves
    return render(request, 'hr_portal/leave_list.html', {'leaves': leaves})


@login_required
@user_passes_test(lambda u: u.is_hr or u.is_superuser)
def hr_leave_approve(request, pk):
    leave = get_object_or_404(Leave, pk=pk)
    if leave.status == 'Pending':  # Only pending leaves can be approved
        if request.method == 'POST':
            leave.status = 'Approved'
            leave.approved_by = request.user
            leave.approval_date = now()
            leave.save()

            employee = leave.employee  # Get the employee
            duration = leave.duration()  # Get the duration of the leave
            leave_type = leave.leave_type  # Get the leave type

            print(f"Leave Type: {leave_type}, Duration: {duration}, Type of Duration: {type(duration)}") # Add this line

            # Update the employee's leave balance
            employee.update_leave_balance(leave_type, duration, action='deduct')

            messages.success(request, f"Leave request for {leave.employee} approved.")
            return redirect('hr_portal:hr_leave_list')
        return render(request, 'hr_portal/leave_approve_confirm.html', {'leave': leave})
    else:
        messages.error(request, f"Leave request for {leave.employee} is not pending.")
        return redirect('hr_portal:hr_leave_list')

@login_required
@user_passes_test(lambda u: u.is_hr or u.is_superuser)
def hr_leave_reject(request, pk):
    leave = get_object_or_404(Leave, pk=pk)
    if leave.status == 'Pending': #Only pending leaves can be rejected
        if request.method == 'POST':
            leave.status = 'Rejected'
            leave.approved_by = request.user
            leave.approval_date = now()
            leave.save()
            messages.success(request, f"Leave request for {leave.employee} rejected.")
            return redirect('hr_portal:hr_leave_list')
        return render(request, 'hr_portal/leave_reject_confirm.html', {'leave': leave})
    else:
        messages.error(request, f"Leave request for {leave.employee} is not pending.")
        return redirect('hr_portal:hr_leave_list')