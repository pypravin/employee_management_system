from django.contrib import admin
from .models import Notification, Event, NotificationRecipient, Announcement

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'created_at', 'is_urgent', 'is_active')
    search_fields = ('title', 'message')
    list_filter = ('is_urgent', 'is_active')

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'event_date', 'location', 'created_by', 'created_at', 'is_active')
    search_fields = ('title', 'description', 'location')
    list_filter = ('event_date', 'is_active')

@admin.register(NotificationRecipient)
class NotificationRecipientAdmin(admin.ModelAdmin):
    list_display = ('notification', 'recipient', 'is_read', 'read_at')
    search_fields = ('recipient__username', 'notification__title')
    list_filter = ('is_read',)

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'created_at')
    search_fields = ('title', 'content')
    list_filter = ('created_at',)
