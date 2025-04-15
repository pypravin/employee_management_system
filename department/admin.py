from django.contrib import admin
from .models import Department

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_by', 'updated_by', 'created_at', 'updated_at', 'is_active')
    search_fields = ('name', 'description', 'created_by__username', 'updated_by__username')
    list_filter = ('is_active', 'created_at', 'updated_at')
    ordering = ('name',)
    readonly_fields = ('created_by', 'updated_by', 'created_at', 'updated_at')  # Prevents manual edits

    def save_model(self, request, obj, form, change):
        """Automatically set `created_by` and `updated_by`."""
        if not obj.pk:  # If creating a new department
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
