from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.views import PasswordChangeView
from django.urls import reverse_lazy
from datetime import timedelta  
from django.utils import timezone
from notifications.models import Notification, Announcement, NotificationRecipient, Event
from department.models import Department
from employee.models import Employee
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.contrib.auth import update_session_auth_hash
from leaves.models import Leave
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import redirect
from django.db.models import Count


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
def employee_dashboard(request):
    if request.user.first_login:
        return redirect('force_password_change')

    # Fetch latest 5 announcements
    announcements = Announcement.objects.order_by('-created_at')[:5]

    # Fetch latest 5 notifications for the logged-in user
    user_notifications = NotificationRecipient.objects.filter(
        recipient=request.user,
        notification__is_active=True
    ).order_by('-notification__created_at')[:5]
    #Fetch past leave requests
    leave_history = Leave.objects.filter(employee=request.user).order_by('-applied_at')[:5]
    # Fetch latest 5 events where the employee is an attendee or belongs to the department
    user_department = request.user.department  # Ensure this field exists
    events = Event.objects.filter(
        Q(attendees=request.user) | Q(departments=user_department)
    ).distinct().order_by('-event_date')[:5]

    # Fetch the Employee object
    try:
        employee = Employee.objects.get(work_email=request.user.work_email)
    except Employee.DoesNotExist:
        employee = None

    # Fetch leave request counts by status
    leave_status_counts = Leave.objects.filter(employee=request.user).values('status').annotate(count=Count('id'))
    pending_leaves = 0
    approved_leaves = 0
    rejected_leaves = 0
    cancelled_leaves = 0
    for item in leave_status_counts:
        if item['status'] == 'Pending':
            pending_leaves = item['count']
        elif item['status'] == 'Approved':
            approved_leaves = item['count']
        elif item['status'] == 'Rejected':
            rejected_leaves = item['count']
        elif item['status'] == 'Cancelled':
            cancelled_leaves = item['count']

    return render(request, 'employee_portal/employee_dashboard.html', {
        'announcements': announcements,
        'notifications': user_notifications,
        'events': events,
        'leave_history': leave_history,
        'employee': employee,  # Pass the Employee object to the context
        'annual_leave_balance': employee.annual_leave_balance if employee else None,
        'sick_leave_balance': employee.sick_leave_balance if employee else None,
        'pending_leaves': pending_leaves,
        'approved_leaves': approved_leaves,
        'rejected_leaves': rejected_leaves,
        'cancelled_leaves': cancelled_leaves,
    })


@login_required
def employee_profile(request):
    employee = request.user  # Get the logged-in employee
    return render(request, "employee_portal/employee_profile.html", {"employee": employee})


class ForcePasswordChangeView(PasswordChangeView):

    template_name = 'employee_portal/force_password_change.html'
    success_url = reverse_lazy('employee_dashboard')

    def form_valid(self, form):
        response = super().form_valid(form)

        # Mark first login as False after password change
        self.request.user.first_login = False
        self.request.user.save()

        messages.success(self.request, "Password changed successfully! You can now access your account.")
        return response


