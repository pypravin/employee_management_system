from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import now
from .models import Attendance
from employee.models import Employee
import subprocess
import os
import sys
import datetime
from django.db.models import Q
from django.utils import timezone
from department.models import Department
from leaves.utils import is_employee_on_leave
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger



# Ensure 'attendance/attendance_list.html' template exists for the attendance list view
def attendance_page(request):
    """Render HR dashboard with manual attendance option only if facial recognition fails."""
    show_manual_attendance = request.GET.get("facial_failed", "false") == "true"
    return render(request, "attendance/face_attendance.html", {"show_manual_attendance": show_manual_attendance})




def start_face_recognition(request):
    """Trigger face recognition, record attendance, and handle failures."""
    try:
        script_path = r"D:\soft_proj\employee_management_system\attendance\recognize_faces.py"
        python_exec = sys.executable

        process = subprocess.Popen([python_exec, script_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

        output_message = stdout.decode(errors="ignore") if stdout else "Face recognition completed."
        error_message = stderr.decode(errors="ignore") if stderr else None

        if error_message:
            print(f"❌ Errors:\n{error_message}")

        if "No match found" in output_message or "Error" in output_message:
            return JsonResponse({"success": False, "message": "Face not recognized."}, status=200) # Changed status to 200

        recognized_employee_id = None
        for line in output_message.split("\n"):
            if "Recognized Employee ID:" in line:
                recognized_employee_id = line.split(":")[-1].strip()
                break

        if recognized_employee_id:
            try:
                employee = Employee.objects.get(id=recognized_employee_id)
                today = timezone.now().date()
                time_now = timezone.now().time()

                if is_employee_on_leave(employee):
                    return JsonResponse({"success": False, "message": "Employee is on leave, attendance not recorded."}, status=200)

                attendance, created = Attendance.objects.get_or_create(
                    employee=employee, date=today, defaults={"method": "Facial"}
                )

                if created or not attendance.time_in:
                    attendance.time_in = time_now

                attendance.save()
                return JsonResponse({"success": True, "redirect_url": "/attendance/attendance_list/"}, status=200)

            except Employee.DoesNotExist:
                return JsonResponse({"success": False, "message": f"Employee with ID {recognized_employee_id} not found."}, status=200)

        return JsonResponse({"success": False, "message": "No employee recognized."}, status=200)

    except Exception as e:
        print(f"Error in start_face_recognition: {e}")
        return JsonResponse({"success": False, "message": "Error during face recognition."}, status=200)

def manual_attendance(request):
    return render(request, "attendance/manual_attendance.html", {"today": now().date()})

def search_employee(request):
    query = request.GET.get("q", "")
    if query:
        employees = Employee.objects.filter(
            Q(first_name__istartswith=query) | Q(last_name__istartswith=query) | Q(department__name__icontains=query),
            is_active=True
        )[:10]
        data = [
            {
                "id": str(emp.id),
                "first_name": emp.first_name,
                "last_name": emp.last_name,
                "department": emp.department.name if emp.department else "No Department"
            }
            for emp in employees
        ]
        return JsonResponse(data, safe=False)
    return JsonResponse([], safe=False)



@csrf_exempt
def record_attendance(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method."}, status=400)

    employee_id = request.POST.get("employee_id")
    date_str = request.POST.get("date")
    time_in_str = request.POST.get("time_in")
    time_out_str = request.POST.get("time_out")
    method = request.POST.get("method") or "Manual"  # Default to Manual

    try:
        employee = get_object_or_404(Employee, id=employee_id)

        # Check if the employee is on leave
        if is_employee_on_leave(employee):
            return JsonResponse({"error": f"{employee.full_name} is on approved leave. Manual attendance cannot be recorded."}, status=400)

        # Validate and parse date
        try:
            date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else timezone.now().date()
        except (ValueError, TypeError):
            return JsonResponse({"error": "Invalid date format."}, status=400)

        today = timezone.now().date()

        # Prevent future attendance
        if date > today:
            return JsonResponse({"error": "Cannot record attendance for a future date."}, status=400)

        # (Optional) Prevent past attendance records
        if date < today:
            return JsonResponse({"error": "Cannot record attendance for past dates."}, status=400)

        # Get or create attendance record
        attendance, created = Attendance.objects.get_or_create(
            employee=employee,
            date=date,
            defaults={"method": method}  # Ensures correct method on creation
        )

        # Update method if necessary
        if not created and attendance.method != method:
            attendance.method = method

        # Validate and parse time
        try:
            time_in = datetime.datetime.strptime(time_in_str, "%H:%M").time() if time_in_str else None
            time_out = datetime.datetime.strptime(time_out_str, "%H:%M").time() if time_out_str else None
        except ValueError:
            return JsonResponse({"error": "Invalid time format."}, status=400)

        # Prevent duplicate 'Time In' entries
        if time_in:
            if attendance.time_in:
                return JsonResponse({"error": "Time In already recorded for this employee today."}, status=400)
            attendance.time_in = time_in

        # Ensure 'Time Out' is not set before 'Time In'
        if time_out:
            if not attendance.time_in:
                return JsonResponse({"error": "Cannot set Time Out without Time In."}, status=400)
            if time_in and time_out <= time_in:
                return JsonResponse({"error": "Time Out cannot be before or equal to Time In."}, status=400)
            attendance.time_out = time_out

        attendance.save()
        return JsonResponse({"success": True, "message": "Attendance recorded successfully."})

    except Employee.DoesNotExist:
        return JsonResponse({"error": "Employee not found."}, status=400)
    except Exception as e:
        print(f"Error in record_attendance: {e}")
        return JsonResponse({"error": "An unexpected error occurred."}, status=500)

@login_required
def get_employee_attendance(request):
    employee_id = request.GET.get("employee_id")
    date = timezone.now().date()

    try:
        attendance = Attendance.objects.get(employee_id=employee_id, date=date)
        return JsonResponse({"time_in": attendance.time_in.strftime("%H:%M") if attendance.time_in else None})
    except Attendance.DoesNotExist:
        return JsonResponse({"time_in": None})


@login_required
def attendance_list(request):
    date_range = request.GET.get("date_range", "")
    employee_search = request.GET.get("employee_search", "")
    department_id = request.GET.get("department", "")
    attendance_method = request.GET.get("method", "")

    attendance_records = Attendance.objects.select_related("employee", "employee__department").all().order_by('-date', '-time_in')

    if date_range:
        dates = date_range.split(",")
        if len(dates) == 2:
            try:
                start_date, end_date = dates
                attendance_records = attendance_records.filter(date__range=[start_date, end_date])
            except ValueError:
                pass

    if employee_search:
        attendance_records = attendance_records.filter(
            Q(employee__first_name__icontains=employee_search) |
            Q(employee__last_name__icontains=employee_search)
        )

    if department_id.isdigit():
        attendance_records = attendance_records.filter(employee__department_id=int(department_id))

    for record in attendance_records:
        record.employee.is_on_leave = is_employee_on_leave(record.employee)

    departments = Department.objects.all()

    # Pagination logic
    paginator = Paginator(attendance_records, 8)  # Show 10 records per page
    page = request.GET.get('page')

    try:
        attendance_records = paginator.page(page)
    except PageNotAnInteger:
        attendance_records = paginator.page(1)
    except EmptyPage:
        attendance_records = paginator.page(paginator.num_pages)

    context = {
        "attendance_records": attendance_records,
        "departments": departments,
    }
    return render(request, "attendance/attendance_list.html", context)


from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.management import call_command
from django.shortcuts import render

@csrf_exempt
def train_facial_model_view(request):
    try:
        call_command('train_facial_model')
        message = "Facial model trained successfully!"
        status = "success"
    except Exception as e:
        message = f"Error training facial model: {str(e)}"
        status = "error"

    # Pass the status and message to the template
    return render(request, 'hr_portal/hr_dashboard.html', {'status': status, 'message': message})



def get_attendance_details(request, id):
    attendance = get_object_or_404(Attendance, id=id)
    
    # If the request is AJAX (for modal)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, "attendance/attendance_detail_partial.html", {"attendance": attendance})

    # If the request is not AJAX, return JSON (for debugging or API use)
    data = {
        "id": attendance.id,
        "employee": f"{attendance.employee.first_name} {attendance.employee.last_name}",
        "department": attendance.employee.department.name if attendance.employee.department else "N/A",
        "date": attendance.date.strftime("%Y-%m-%d"),
        "time_in": attendance.time_in.strftime("%H:%M:%S") if attendance.time_in else "-",
        "time_out": attendance.time_out.strftime("%H:%M:%S") if attendance.time_out else "-",
        "method": "Facial Recognition" if attendance.method == "facial" else "Manual",
        "face_image": attendance.face_image.url if attendance.face_image else None,
    }
    return JsonResponse(data)  # Optional JSON fallback

def get_latest_attendance(request):
    """API View to get the latest attendance records."""
    try:
        attendance_records = Attendance.objects.select_related('employee', 'employee__department') \
                                               .order_by('-date', '-time_in')[:10]

        data = []
        for record in attendance_records:
            time_in = record.time_in.strftime("%H:%M:%S") if record.time_in else "-"  
            time_out = record.time_out.strftime("%H:%M:%S") if record.time_out else "-"  

            data.append({
                "id": record.id,
                "employee_id": record.employee.display_employee_id,
                "name": f"{record.employee.first_name} {record.employee.last_name}",
                "department": record.employee.department.name if record.employee.department else "N/A",
                "date": record.date.strftime("%Y-%m-%d"),
                "time_in": time_in,  
                "time_out": time_out,
                "method": record.method
            })

        return JsonResponse({"status": "success", "data": data})

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)})


from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from attendance.models import Attendance  # Import your Attendance model
from employee.models import Employee  # Import your Employee model

@login_required
def employee_attendance_history(request):
    """Displays the attendance history for the logged-in employee."""
    try:
        # Fetch the Employee object using the work_email of the logged-in user
        employee = Employee.objects.get(work_email=request.user.work_email)
        attendance_records = Attendance.objects.filter(employee=employee).order_by('-date', '-time_in')
        context = {
            'attendance_records': attendance_records,
        }
        return render(request, 'attendance/employee_attendance_history.html', context)  # Updated template path
    except Employee.DoesNotExist:
        # Handle the case where no Employee profile is found for the logged-in user
        context = {
            'error_message': "Your employee profile could not be found.",
        }
        return render(request, 'attendance/employee_attendance_history.html', context)  # Updated template path
    except Exception as e:
        # Handle other potential errors
        context = {
            'error_message': f"An error occurred: {e}",
        }
        return render(request, 'attendance/employee_attendance_history.html', context)  # Updated template path


from django.shortcuts import render
from employee.models import Employee
from attendance.models import Attendance
from leaves.models import Leave
from django.utils import timezone

def absent_list(request):
    today = timezone.now().date()

    # Get all active employees
    all_active_employees = Employee.objects.filter(is_active=True, is_deleted=False)

    # Get employees who have recorded attendance today
    present_employees_today = Attendance.objects.filter(date=today).values_list('employee_id', flat=True).distinct()

    # Get employees who are on approved leave today
    on_leave_employees_today = Leave.objects.filter(
        status='Approved',
        start_date__lte=today,
        end_date__gte=today
    ).values_list('employee_id', flat=True).distinct()

    # Identify absent employees: those active employees who are neither present nor on leave
    absent_employees = [
        emp for emp in all_active_employees
        if emp.id not in present_employees_today and emp.id not in on_leave_employees_today
    ]

    context = {
        'absent_employees': absent_employees,
        'today': today,
    }
    return render(request, 'attendance/absent_list.html', context)