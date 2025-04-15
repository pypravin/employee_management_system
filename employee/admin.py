from django.contrib import admin
from .models import Employee

class EmployeeAdmin(admin.ModelAdmin):  # Inherit from admin.ModelAdmin
    list_display = ('display_employee_id', 'first_name', 'last_name',
                    'department', 'designation', 'work_email', 'is_active', 'facial_enrollment_status', 'hire_date', 'first_login') # Added first_login to list_display
    list_filter = ('department', 'is_active', 'facial_enrollment_status') # Added facial_enrollment_status to filters
    search_fields = ('first_name', 'last_name', 'display_employee_id',
                     'work_email')

    fieldsets = (
        (None, {'fields': ('first_name', 'last_name', 'work_email', 'password')}),
        ('Job Information', {'fields': ('department', 'designation',
                                            'hire_date', 'facial_enrollment_status', 'first_login')}), # Added facial_enrollment_status, first_login, and employee_id
        ('Permissions', {'fields': ('is_active', 'is_hr',)}), # Added is_hr, is_staff, is_superuser, groups, user_permissions
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('first_name', 'last_name',
                       'work_email', 'password', 'password', 'department', 'designation', 'hire_date', 'facial_enrollment_status', 'first_login')}), # Added hire_date, facial_enrollment_status, first_login, and employee_id to add_fieldsets
    )

    ordering = ('display_employee_id',)
    readonly_fields = ('display_employee_id',)


admin.site.register(Employee, EmployeeAdmin)