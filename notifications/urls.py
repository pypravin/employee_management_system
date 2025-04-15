from django.urls import path
from . import views

app_name = "notifications"  # IMPORTANT: Set the app_name here to "employee_portal"

urlpatterns = [
    path("notifications/", views.notification_list, name="notification_list"),
    path("notifications/create/", views.notification_create, name="notification_create"),
    path("notifications/<int:pk>/", views.notification_detail, name="notification_detail"), # Keep this for potential HR use
    path("notifications/<int:pk>/update/", views.notification_update, name="notification_update"),
    path("notifications/<int:pk>/delete/", views.notification_delete, name="notification_delete"),
    path("view/<int:notification_id>/", views.view_notification, name="view_notification"),
    path("notifications/mark-all-as-read/", views.mark_notification_as_read, name="mark_all_notifications_as_read"),

    path("events/", views.event_list, name="event_list"),
    path("events/create/", views.event_create, name="event_create"),
    path("events/<int:pk>/", views.event_detail, name="event_detail"), # Keep this for potential HR use
    path("events/<int:pk>/update/", views.event_update, name="event_update"),
    path("events/<int:pk>/delete/", views.event_delete, name="event_delete"),

    # Employee specific views and URLs - NOW IN NOTIFICATIONS APP
    path('notifications/view/<int:notification_id>/', views.view_employee_notification, name='view_employee_notification'),
    path('notifications/latest/', views.employee_notification, name='employee_notification'),
    path('events/<int:pk>/', views.employee_event_detail_view, name='employee_event_detail'),
    path('events/registered/', views.registered_events, name='registered_events'),

    # emploee specific notifications (Consider if this is redundant with the above)
    path('notification/<int:pk>/', views.employee_notification_detail, name='employee_notification_detail'),

    # marks notification as read (Consider if this is redundant with the above)
    path('notifications/mark-as-read/', views.mark_notification_as_read, name='mark_notification_as_read'),
    # Employee event registration (Consider if this should also be under employee_portal namespace)
    path("events/register/<int:event_id>/", views.register_for_event, name="register_for_event"),
    path("events/check-registration/<int:event_id>/", views.check_event_registration, name="check_event_registration"),

    # Employee registered events (Consider if this is redundant)
    path("events/my-events/", views.registered_events, name="registered_events"), # You might want to remove this to avoid conflict
    path('events/all/', views.employee_event_list, name='employee_event_list'),
    # Employee event detail view (Consider if this is redundant)
    path("events/employee/detail/<int:pk>/", views.employee_event_detail_view, name="employee_event_detail"), # You might want to remove this to avoid conflict
]