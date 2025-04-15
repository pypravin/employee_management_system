from django.db.models.signals import post_save
from django.dispatch import receiver
from notifications.models import Notification, Event, Announcement, NotificationRecipient
from employee.models import Employee
import logging
import sys

# Set up logging with UTF-8 encoding
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

@receiver(post_save, sender=Event)
def create_notification_for_event(sender, instance, created, **kwargs):
    """Automatically create/update a notification when an event is created or updated by HR."""
    logger.info(f"Event saved: {instance.title}, Created: {created}")

    if not instance.created_by or not instance.created_by.is_hr:
        logger.warning(f"Event '{instance.title}' creation/update blocked! Only HR can perform this action.")
        return

    try:
        notification = Notification.objects.get(event=instance)
        logger.info(f"Notification found for event '{instance.title}', updating recipients.")
        # Clear existing recipients and re-add based on current attendees
        notification.recipients.clear()
    except Notification.DoesNotExist:
        notification = Notification.objects.create(
            title=f"New Event: {instance.title}",
            message=f"An event has been scheduled: {instance.description}",
            event=instance,
            created_by=instance.created_by
        )
        logger.info(f"Notification created for event '{instance.title}'.")

    active_employees = Employee.objects.filter(is_active=True, is_hr=False)
    attendees = set()

    if instance.select_all_employees:
        attendees.update(active_employees)
        logger.info(f"Notification '{instance.title}' will be sent to ALL active employees.")
    elif instance.attendees.exists():
        attendees.update(instance.attendees.filter(is_active=True, is_hr=False))
        logger.info(f"Notification '{instance.title}' will be sent to selected attendees.")
    elif instance.departments.exists():
        employees_from_departments = Employee.objects.filter(
            department__in=instance.departments.all(),
            is_active=True,
            is_hr=False
        )
        attendees.update(employees_from_departments)
        logger.info(f"Notification '{instance.title}' will be sent to employees in selected departments.")
    else:
        attendees.update(active_employees)  # Default to all active employees

    # Assign recipients to the notification
    notification.recipients.set(attendees)
    logger.debug(f"✅ Notification '{notification.title}' assigned to: {list(notification.recipients.all().values_list('work_email', flat=True))}")

    # Consider updating the notification message if the event details change
    notification.message = f"An event has been scheduled: {instance.description} on {instance.event_date} at {instance.location}"
    notification.save()

@receiver(post_save, sender=Announcement)
def create_notification_for_announcement(sender, instance, created, **kwargs):
    """Automatically create a notification when an announcement is created by HR."""
    logger.info(f"Announcement saved: {instance.title}")

    if created:
        if not instance.created_by or not instance.created_by.is_hr:
            logger.warning(f"Announcement '{instance.title}' creation blocked! Only HR can create announcements.")
            return

        if not Notification.objects.filter(announcement=instance).exists():
            notification = Notification.objects.create(
                title=f"New Announcement: {instance.title}",
                message=instance.content,
                announcement=instance,
                created_by=instance.created_by
            )

            active_employees = Employee.objects.filter(is_active=True, is_hr=False)
            notification.recipients.add(*active_employees)
            logger.info(f"Notification for announcement '{instance.title}' sent to all active employees.")
