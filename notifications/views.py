from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Notification, Event, NotificationRecipient , EventRegistration
from .forms import NotificationForm, EventForm
from django.db.models import Q
from django.utils.timezone import now
from django.utils.dateparse import parse_date
from employee.models import Employee
from department.models import Department
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.core.paginator import Paginator
from django.urls import reverse


from django.contrib.auth.decorators import user_passes_test

def is_hr(user):
    try:
        employee = Employee.objects.get(work_email=user.work_email)  # Match with your authentication field
        return employee.is_hr  # Assuming 'is_hr' is a BooleanField in your Employee model
    except Employee.DoesNotExist:
        return False

# List Notifications
def notification_list(request):
    notifications = Notification.objects.filter(is_active=True).order_by('-created_at')

    # Get filter parameters
    search_query = request.GET.get("search", "").strip()
    urgency_filter = request.GET.get("urgency")
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    # Apply filters
    if search_query:
        notifications = notifications.filter(title__icontains=search_query)

    if urgency_filter in ["1", "0"]:
        notifications = notifications.filter(is_urgent=(urgency_filter == "1"))

    if start_date:
        notifications = notifications.filter(created_at__date__gte=parse_date(start_date))
    if end_date:
        notifications = notifications.filter(created_at__date__lte=parse_date(end_date))

    # Fetch all recipients for the filtered notifications in a single query
    recipients = NotificationRecipient.objects.filter(notification__in=notifications).select_related('recipient')

    # Create a mapping for read/unread recipients
    notification_data = {n: {'read_by': [], 'unread_by': []} for n in notifications}

    for recipient in recipients:
        if recipient.is_read:
            notification_data[recipient.notification]['read_by'].append(recipient.recipient)
        else:
            notification_data[recipient.notification]['unread_by'].append(recipient.recipient)

    # Merge notification data
    notifications_with_read_status = [
        {
            'notification': notification,
            'read_by': notification_data[notification]['read_by'],
            'unread_by': notification_data[notification]['unread_by'],
        }
        for notification in notifications
    ]

    # Pagination
    paginator = Paginator(notifications_with_read_status, 10)  # Show 10 per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, "notifications/notification_list.html", {
        "notifications": page_obj,  # Use paginated results
        "search_query": search_query,
        "urgency_filter": urgency_filter,
        "start_date": start_date,
        "end_date": end_date,
    })

import logging
logger = logging.getLogger(__name__)

from notifications.models import NotificationRecipient

# Create Notification
@login_required
@user_passes_test(is_hr)
def notification_create(request):
    if request.method == "POST":
        form = NotificationForm(request.POST)
        if form.is_valid():
            notification = form.save()  # Save the notification first

            intended_recipients = set()

            # Add selected employees
            selected_employees = form.cleaned_data['recipients']
            logger.info(f"Selected Employees: {selected_employees}")
            intended_recipients.update(selected_employees)

            # Add employees from selected departments
            selected_departments = form.cleaned_data['departments']
            logger.info(f"Selected Departments: {selected_departments}")
            employees_from_departments = Employee.objects.filter(department__in=selected_departments, is_active=True)
            logger.info(f"Employees from Departments: {employees_from_departments}")
            intended_recipients.update(employees_from_departments)

            # Assign all intended recipients using bulk_create
            logger.info(f"Intended Recipients (before bulk_create): {intended_recipients}")
            recipients_to_create = [
                NotificationRecipient(notification=notification, recipient=employee)
                for employee in intended_recipients
            ]
            NotificationRecipient.objects.bulk_create(recipients_to_create)
            logger.info(f"Number of recipients created: {NotificationRecipient.objects.filter(notification=notification).count()}")

            messages.success(request, "Notification created successfully.", extra_tags="success notification")
            return redirect("notifications:notification_list")
    else:
        form = NotificationForm()
    return render(request, "notifications/notification_form.html", {"form": form, "title": "Create Notification"})

# Update Notification
@login_required
@user_passes_test(is_hr)
def notification_update(request, pk):
    notification = get_object_or_404(Notification, pk=pk)

    if request.method == "POST":
        form = NotificationForm(request.POST, instance=notification)
        if form.is_valid():
            notification = form.save(commit=False)
            notification.save()

            # ✅ Clear previous recipients & add new ones
            notification.recipients.clear()
            selected_employees = form.cleaned_data['recipients']
            notification.recipients.set(selected_employees)

            # ✅ Assign employees from selected departments (Clearing old department-based recipients)
            selected_departments = form.cleaned_data['departments']
            employees_from_departments = Employee.objects.filter(department__in=selected_departments, is_active=True)
            notification.recipients.add(*employees_from_departments)

            messages.success(request, f'Notification "{notification.title}" updated successfully.', extra_tags="success notification")
            return redirect("notifications:notification_list")

    else:
        form = NotificationForm(instance=notification)

    return render(request, "notifications/notification_form.html", {"form": form, "title": "Update Notification"})

# Notification Details
def notification_detail(request, pk):
    notification = get_object_or_404(Notification, pk=pk)

    # Get recipients & their read status
    recipients = NotificationRecipient.objects.filter(notification=notification)
    read_by = [r.recipient for r in recipients if r.is_read]
    unread_by = [r.recipient for r in recipients if not r.is_read]

    return render(request, "notifications/notification_detail.html", {
        "notification": notification,
        "read_by": read_by, 
        "unread_by": unread_by,  
    })

# View Notification
@login_required
def view_notification(request, notification_id):
    # ✅ Fetch Notification object
    notification = get_object_or_404(Notification, id=notification_id)

    # ✅ Get NotificationRecipient to mark as read
    notification_recipient = NotificationRecipient.objects.filter(
        recipient=request.user, notification=notification
    ).first()

    if notification_recipient and not notification_recipient.is_read:
        notification_recipient.is_read = True
        notification_recipient.save()

    # ✅ Debugging logs
    print(f"Notification ID: {notification.id}")
    print(f"Title: {notification.title}")
    print(f"Linked Event: {notification.event}")  
    print(f"Linked Announcement: {notification.announcement}")

    # ✅ Redirect if the notification is linked to an event or announcement
    if notification.event:
        print("🔀 Redirecting to Event Page")
        return redirect("employee_portal/employee_event_detail", pk=notification.event.id)
    elif notification.announcement:
        print("🔀 Redirecting to Announcement Page")
        return redirect("notifications:employee_notification_detail", pk=notification.announcement.id)

    # ✅ Otherwise, show the notification details
    print("🔀 Showing Notification Detail Page")
    return render(request, "notifications/employee_notification_detail.html", {"notification": notification})


# List Events
@login_required
def event_list(request):
    events = Event.objects.filter(is_active=True).order_by('-event_date')

    # Get filter parameters
    search_query = request.GET.get("search", "").strip()
    date_filter = request.GET.get("date_filter")
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")
    location = request.GET.get("location")

    # Apply filters
    if search_query:
        events = events.filter(title__icontains=search_query)

    if date_filter == "upcoming":
        events = events.filter(event_date__gte=now())  # Upcoming events
    elif date_filter == "past":
        events = events.filter(event_date__lt=now())  # Past events

    if start_date:
        events = events.filter(event_date__date__gte=parse_date(start_date))
    if end_date:
        events = events.filter(event_date__date__lte=parse_date(end_date))

    if location:
        events = events.filter(location__icontains=location)

    return render(request, "notifications/event_list.html", {
        "events": events,
        "search_query": search_query,
        "date_filter": date_filter,
        "start_date": start_date,
        "end_date": end_date,
        "location": location,
    })

import logging

logger = logging.getLogger(__name__)
@login_required
@user_passes_test(is_hr)
def event_create(request):
    if request.method == "POST":
        logger.debug(f"📝 Raw POST Data: {request.POST}")

        form = EventForm(request.POST)

        print(f"Form is valid: {form.is_valid()}")  # Debugging line
        if form.is_valid():
            print(f"Cleaned data: {form.cleaned_data}") # Debugging line
            event = form.save(commit=False)
            event.created_by = request.user
            event.save()

            # Extract attendees and departments
            selected_attendees = form.cleaned_data.get("attendees")
            selected_departments = form.cleaned_data.get("departments")
            select_all_employees = form.cleaned_data.get("select_all_employees")
            select_all_departments = form.cleaned_data.get("select_all_departments")

            logger.debug(f"✅ Select All Employees: {select_all_employees}")
            logger.debug(f"✅ Select All Departments: {select_all_departments}")

            # Assign attendees based on selection
            if select_all_employees:
                all_employees = Employee.objects.filter(is_active=True)
                event.attendees.set(all_employees)
                logger.debug(f"🎯 All employees assigned: {list(all_employees.values_list('work_email', flat=True))}")
            else:
                event.attendees.set(selected_attendees if selected_attendees else [])

            # Assign department-based employees
            if select_all_departments:
                employees_from_departments = Employee.objects.filter(is_active=True)
            else:
                employees_from_departments = Employee.objects.filter(department__in=selected_departments, is_active=True)

            event.attendees.add(*employees_from_departments)


            # Assign recipients
            notification.recipients.set(event.attendees.all())

            logger.debug(f"✅ Notification '{notification.title}' assigned to: {list(notification.recipients.all().values_list('work_email', flat=True))}")

            messages.success(request, "Event created successfully.", extra_tags="success event")
            return redirect("notifications:event_list")
        else:
            logger.debug(f"❌ Form Errors: {form.errors}")
    else:
        form = EventForm()

    return render(request, "notifications/event_form.html", {"form": form, "title": "Create Event"})


@login_required
@user_passes_test(is_hr)
def event_update(request, pk):
    event = get_object_or_404(Event, pk=pk)

    if request.method == "POST":
        form = EventForm(request.POST, instance=event)
        if form.is_valid():
            event = form.save(commit=False)
            event.save()

            # ✅ Clear previous attendees & departments before updating
            event.attendees.clear()
            selected_attendees = form.cleaned_data['attendees']
            event.attendees.set(selected_attendees)

            selected_departments = form.cleaned_data['departments']
            employees_from_departments = Employee.objects.filter(department__in=selected_departments, is_active=True)
            event.attendees.add(*employees_from_departments)

            messages.success(request, f'Event "{event.title}" updated successfully.', extra_tags="success event")
            return redirect("notifications:event_list")

    else:
        form = EventForm(instance=event)

    return render(request, "notifications/event_form.html", {"form": form, "title": "Update Event"})

# Event Details
def event_detail(request, pk):
    event = get_object_or_404(Event, pk=pk)
    return render(request, "notifications/event_detail.html", {"event": event})


# employee specific notifications
@login_required
def employee_notification(request):
    """Displays the latest notifications for the logged-in employee."""
    latest_notifications = NotificationRecipient.objects.filter(recipient=request.user).order_by('-notification__created_at')[:5] # Get the 5 latest
    context = {
        'latest_notifications': latest_notifications,
    }
    return render(request, 'notifications/latest_notifications.html', context)


@login_required
def employee_notification_detail(request, pk):
    # 🔹 Fetch NotificationRecipient, not Notification
    recipient = get_object_or_404(NotificationRecipient, id=pk, recipient=request.user)
    print(f"Recipient: {recipient}")  # Debugging

    # 🔹 Mark Notification as Read
    if not recipient.is_read:
        recipient.is_read = True
        recipient.read_at = now()
        recipient.save()

    # 🔹 Get Notification Details
    notification = recipient.notification
    print(f"Notification: {notification}")  # Debugging

    # 🔹 Redirect if the notification is linked to an event or announcement
    if notification.event:
        print(f"Redirecting to event: {notification.event.id}")  # Debugging
        return redirect("notifications:event_detail", pk=notification.event.id)
    elif notification.announcement:
        print(f"Redirecting to announcement: {notification.announcement.id}")  # Debugging
        return redirect("notifications:announcement_detail", pk=notification.announcement.id)

    # 🔹 Show notification details if no redirection occurs
    return render(request, 'notifications/employee_notification_detail.html', {'notification': notification})

@login_required
def mark_notification_as_read(request):
    """Marks an announcement or event notification as read and redirects back."""
    if request.method == "POST":
        notification_id = request.POST.get("notification_id")

        if not notification_id:
            # Consider what to do if the ID is missing, maybe a message?
            return redirect("notifications:employee_notification")  # Redirect back anyway

        try:
            notification_recipient = get_object_or_404(
                NotificationRecipient,
                notification__id=notification_id,
                recipient=request.user
            )
            if not notification_recipient.is_read:
                notification_recipient.is_read = True
                notification_recipient.save()
        except NotificationRecipient.DoesNotExist:
            # Handle the case where the recipient doesn't have this notification
            pass  # Or log the error

        return redirect("notifications:employee_notification")  # Redirect back to the notification list

    return redirect("notifications:employee_notification")  # Redirect for GET requests as well

    
@login_required
def register_for_event(request, event_id):
    """Registers an employee for an event."""
    # Fetch the event using the provided event_id or return 404 if not found
    event = get_object_or_404(Event, id=event_id)
    
    # Check if the event is active (only allow registration for active events)
    if not event.is_active:
        messages.error(request, "This event is no longer active and cannot be registered for.", extra_tags="event-error")
        return redirect("employee_event_list")  # Redirect to event list if the event is inactive

    # Check if the employee is already registered for the event
    if EventRegistration.objects.filter(event=event, employee=request.user).exists():
        messages.error(request, "You are already registered for this event.", extra_tags="event-error")
        return redirect("notifications:employee_event_detail", pk=event.id)  # Redirect back to event detail if already registered

    # Register the employee for the event
    try:
        # Create a registration entry and add the employee to the event's attendees
        EventRegistration.objects.create(event=event, employee=request.user)
        event.attendees.add(request.user)  # Add employee to the event attendees list
        messages.success(request, "Successfully registered for the event!", extra_tags="event-success")
    except Exception as e:
        # If any error occurs during registration, show an error message
        messages.error(request, f"An error occurred while registering: {str(e)}", extra_tags="event-error")
        return redirect("notificcations:employee_event_detail", pk=event.id)

    # Redirect to the event detail page after successful registration
    return redirect("notifications:employee_event_detail", pk=event.id)



@login_required
def check_event_registration(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    is_registered = EventRegistration.objects.filter(event=event, employee=request.user).exists()

    return JsonResponse({"success": True, "is_registered": is_registered})









@login_required
@user_passes_test(is_hr)
def notification_delete(request, pk):
    notification = get_object_or_404(Notification, pk=pk)
    if request.method == "POST":
        notification.delete()
        messages.success(request, f'Notification "{notification.title}" deleted.', extra_tags="danger notification")
        return redirect("notifications:notification_list")
    return render(request, "notifications/notification_delete.html", {"notification": notification})


@login_required
@user_passes_test(is_hr)
def event_delete(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if request.method == "POST":
        event.delete()
        messages.success(request, f'Event "{event.title}" deleted.', extra_tags="danger event")
        return redirect("notifications:event_list")
    return render(request, "notifications/event_delete.html", {"event": event})




@login_required
def view_employee_notification(request, notification_id):
    # Get the NotificationRecipient object
    notification_recipient = get_object_or_404(NotificationRecipient, id=notification_id)

    # Get the actual Notification object from the recipient
    notification = notification_recipient.notification

    return render(request, 'notifications/employee_notification_detail.html', {'notification': notification})
# employee specific events
@login_required
def registered_events(request):
    """Displays a list of events the logged-in employee is registered for."""
    registrations = EventRegistration.objects.filter(employee=request.user).order_by('-event__event_date')
    registered_events_list = [registration.event for registration in registrations]
    context = {
        'registered_events': registered_events_list,
    }
    return render(request, 'notifications/registered_events.html', context)

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from notifications.models import Event

@login_required
def employee_event_detail_view(request, pk):
    """Displays the details of an event for an employee."""
    event = get_object_or_404(Event, pk=pk)
    return render(request, 'notifications/employee_event_detail.html', {'event': event})


@login_required
def employee_notification(request):
    """Displays the latest notifications for the logged-in employee."""
    latest_notifications = NotificationRecipient.objects.filter(recipient=request.user).order_by('-notification__created_at')[:5] # Get the 5 latest
    context = {
        'latest_notifications': latest_notifications,
    }
    return render(request, 'notifications/latest_notifications.html', context)


# Employee Event Lists
@login_required
def employee_event_list(request):
    """Displays a list of events for the logged-in employee."""
    events = Event.objects.filter(is_active=True).order_by('-event_date')
    context = {
        'events': events,
    }
    return render(request, 'notifications/employee_event_list.html', context)
