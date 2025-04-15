from django.contrib import admin
from .models import AttendanceReport

@admin.register(AttendanceReport)
class AttendanceReportAdmin(admin.ModelAdmin):
    list_display = ('attendance', 'date_generated', 'status', 'method')
    search_fields = ('attendance__employee__first_name', 'attendance__employee__last_name')
