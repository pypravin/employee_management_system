from django.contrib import admin
from .models import Attendance

@admin.register(Attendance)  # Use @admin.register decorator for conciseness
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('employee', 'date', 'time_in', 'time_out', 'method', 'status', 'timestamp')  # Display these fields in the list view
    list_filter = ('employee', 'date', 'method')  # Add filters for these fields
    search_fields = ('employee__display_employee_id', 'employee__first_name', 'employee__last_name') #Search by employee id, first name, last name.
    date_hierarchy = 'date'  # Add date hierarchy for easy filtering by date ranges
    ordering = ('-timestamp',)  # Order by timestamp (most recent first)
    readonly_fields = ('timestamp',)  # Make timestamp read-only (it's auto-generated)

    fieldsets = (  # Customize the form layout
        (None, {'fields': ('employee', 'date', 'method', 'status')}),  # Fields in the first group
        ('Time Details', {'fields': ('time_in', 'time_out')}),  # Fields in the second group (collapsed initially)
    )