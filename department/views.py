from django.shortcuts import render, get_object_or_404, redirect
from .models import Department
from .forms import DepartmentForm
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from employee.models import Employee


def is_hr_or_admin(user):
    if user.is_authenticated:
        if user.is_superuser:  # Superuser always has access
            return True
        try:
            employee = Employee.objects.get(pk=user.pk) # Get the Employee instance
            return employee.is_hr  # Check the is_hr flag
        except Employee.DoesNotExist:
            return False  # User is authenticated but not an Employee
    return False # User is not authenticated

@user_passes_test(is_hr_or_admin)
def department_list(request):
    print(request.user.groups.all())  # Check user groups in the console
    departments = Department.objects.filter(is_active=True)
    return render(request, 'department/department_list.html', {'departments': departments})

@user_passes_test(is_hr_or_admin)
def department_create(request):
    if request.method == "POST":
        form = DepartmentForm(request.POST)
        if form.is_valid():
            department = form.save(commit=False)
            department.created_by = request.user  # Track who created it
            department.updated_by = request.user  # Also set the first updater
            department.save()
            messages.success(request, 'Department has been created successfully.',extra_tags="department_create")
            return redirect("department:department_list")
    else:
        form = DepartmentForm()

    return render(request, "department/department_form.html", {"form": form, "title": "Create Department"})


@user_passes_test(is_hr_or_admin)
def department_update(request, pk):
    department = get_object_or_404(Department, pk=pk)
    
    if request.method == "POST":
        form = DepartmentForm(request.POST, instance=department)
        if form.is_valid():
            department = form.save(commit=False)
            department.updated_by = request.user  # Track last updater
            department.save()
            messages.success(request, f'Department "{department.name}" has been updated successfully.',extra_tags="department_update")
            return redirect("department:department_list")
    else:
        form = DepartmentForm(instance=department)

    return render(request, "department/department_form.html", {"form": form, "title": "Update Department"})


@user_passes_test(is_hr_or_admin)
def department_delete(request, pk):
    department = get_object_or_404(Department, pk=pk)
    if request.method == "POST":
        department.delete()
        messages.success(request, f'Department "{department.name}" has been deleted.',extra_tags="department_delete")
        return redirect("department:department_list")
    return render(request, "department/department_delete.html", {"department": department})

@user_passes_test(is_hr_or_admin)
def deactivate_department(request, department_id):
    department = get_object_or_404(Department, id=department_id)
    if department.is_active:
        department.is_active = False
        department.save()
        messages.success(request, f'Department "{department.name}" has been deactivated.',extra_tags="department_deactivate")
    else:
        messages.warning(request, f'Department "{department.name}" is already deactivated.',extra_tags="department_deactivate")
    
    return redirect('department:department_list')

@user_passes_test(is_hr_or_admin)
def reactivate_department(request, pk):
    department = get_object_or_404(Department, pk=pk)
    if not department.is_active:
        department.is_active = True
        department.save()
        messages.success(request, f'Department "{department.name}" has been reactivated.',extra_tags="department_reactivate")
    return redirect('department:archived_departments')

@user_passes_test(is_hr_or_admin)
def archived_departments(request):
    archived_departments = Department.objects.filter(is_active=False)  # Fetch deactivated departments
    print("Archived Departments:", archived_departments)  # Check output in terminal
    return render(request, 'department/archived_departments.html', {'archived_departments': archived_departments})

