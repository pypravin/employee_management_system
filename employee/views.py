import os
import cv2
import random
import string
import logging
from django.conf import settings
from .forms import EmployeeForm
from .models import Employee
from django.http import JsonResponse
from django.core.mail import send_mail
from django.contrib import messages
from notifications.models import Event
from department.models import Department
from .utils import generate_temp_password
from django.core.paginator import Paginator
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q

import time








def is_hr_or_admin(user):
    if user.is_authenticated:
        if user.is_superuser:  # Check for superuser (admin) status
            return True
        try:
            employee = Employee.objects.get(work_email=user.work_email)  # Assuming email is used to link User and Employee
            return employee.is_hr  # Check if the employee is marked as HR
        except Employee.DoesNotExist:
            return False  # If no Employee found with this email, not HR
    return False

def hr_or_admin_required(view_func):
    decorated_view_func = user_passes_test(is_hr_or_admin, login_url='employee:no_access')(view_func)
    return decorated_view_func


def no_access(request):
    return render(request, "employee/no_access.html")


# Predefined angles for facial capture
ANGLES = [
    "Look Straight", "Look Left", "Look Right", "Look Up", "Look Down",
    "Tilt Left", "Tilt Right", "Look Up Left", "Look Up Right", "Look Down Left"
]

@user_passes_test(is_hr_or_admin)
def register_employee(request):
    if request.method == "POST":
        form = EmployeeForm(request.POST)
        if form.is_valid():
            employee = form.save()  # Save employee data
            return redirect("employee:register_facial", employee_id=employee.display_employee_id)

    else:
        form = EmployeeForm()

    return render(request, "employee/register_employee.html", {"form": form})


@user_passes_test(is_hr_or_admin)
def register_facial(request, employee_id):
    employee = get_object_or_404(Employee, display_employee_id=employee_id)
    return render(request, "employee/register_facial.html", {"employee": employee, "angles": ANGLES})


@user_passes_test(lambda u: u.is_hr or u.is_staff) # Corrected decorator for clarity
def capture_face(request, employee_id):
    employee = get_object_or_404(Employee, display_employee_id=employee_id)
    angle_index = int(request.GET.get('angle_index', 0))
    captures_to_take = int(request.GET.get('captures_to_take', 7))
    captures_taken = 0

    if angle_index >= len(ANGLES):
        employee.facial_enrollment_status = True
        employee.save()
        username = employee.work_email
        temp_password = "".join(random.choices(string.ascii_letters + string.digits, k=10))
        # Assuming send_welcome_email is defined elsewhere
        send_welcome_email(employee, username, temp_password)
        return render(request, "employee/facial_registration_success.html", {"employee": employee})

    current_angle = ANGLES[angle_index]

    # Initialize OpenCV cascades
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_eye.xml")
    # Optional: Load another face cascade for potentially better detection
    # face_cascade_alt = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_profileface.xml")

    cap = cv2.VideoCapture(0)

    image_dir = os.path.join(settings.MEDIA_ROOT, "facial_data", str(employee_id))
    os.makedirs(image_dir, exist_ok=True)

    min_face_size = 50  # Minimum size of a detected face
    max_face_size = 300 # Maximum size of a detected face (adjust based on expected distance)

    while captures_taken < captures_to_take:
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Detect faces with adjusted parameters
        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,  # Increased minNeighbors to reduce false positives
            minSize=(min_face_size, min_face_size),
            maxSize=(max_face_size, max_face_size)
        )

        # # Optional: Detect faces using the alternative cascade as well
        # faces_alt = face_cascade_alt.detectMultiScale(
        #     gray,
        #     scaleFactor=1.1,
        #     minNeighbors=5,
        #     minSize=(min_face_size, min_face_size),
        #     maxSize=(max_face_size, max_face_size)
        # )
        # # Combine the detected faces (remove duplicates if needed)
        # all_faces = list(faces) + list(faces_alt)
        # # To remove duplicates, you might need to convert to tuples and use a set

        # Draw text with the current angle instruction
        cv2.putText(frame, f"Angle: {current_angle}", (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, f"Captures taken: {captures_taken}/{captures_to_take}", (30, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, "Press Q to quit", (30, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        # Display real-time feedback
        if len(faces) > 0:
            cv2.putText(frame, "Face detected, please hold still", (30, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        else:
            cv2.putText(frame, "No face detected, please adjust your position", (30, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        cv2.imshow("Facial Capture", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):  # User pressed 'Q' to quit
            cap.release()
            cv2.destroyAllWindows()
            return render(request, "employee/facial_registration_cancelled.html", {"employee": employee})

        elif len(faces) > 0:
            # Sort faces by size (largest face first)
            faces = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
            x, y, w, h = faces[0]
            face_img = gray[y:y + h, x:x + w]

            # Detect eyes within the face with stricter parameters
            eyes = eye_cascade.detectMultiScale(
                face_img,
                scaleFactor=1.1,
                minNeighbors=3, # Can be lower than face detection
                minSize=(int(w/5), int(h/5)), # Eye size should be a fraction of face size
                maxSize=(int(w/2), int(h/2))
            )

            if len(eyes) >= 2:
                # Basic check if eyes are roughly in the upper half of the face
                eyes_in_upper_half = 0
                for ex, ey, ew, eh in eyes:
                    if ey < h / 2:
                        eyes_in_upper_half += 1

                if eyes_in_upper_half >= 2:
                    # Save the image
                    image_path = os.path.join(image_dir, f"face_{angle_index}_{captures_taken + 1}.jpg")
                    cv2.imwrite(image_path, face_img)
                    print(f"Captured {current_angle} (Capture {captures_taken + 1})")
                    captures_taken += 1
                    time.sleep(0.3)
                else:
                    cv2.putText(frame, "Eyes not detected in the expected region. Please adjust.", (30, 250), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            else:
                cv2.putText(frame, "Less than two eyes detected. Please ensure your face is clearly visible.", (30, 250), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        if captures_taken == captures_to_take:
            cap.release()
            cv2.destroyAllWindows()
            return redirect(f"/employee/capture_face/{employee_id}/?angle_index={angle_index + 1}")

    cap.release()
    cv2.destroyAllWindows()
    return render(request, "employee/register_facial.html", {"employee": employee, "angles": ANGLES, "current_angle_index": angle_index})
email_logger = logging.getLogger("email_logger")

def send_welcome_email(employee, username, temp_password):
    email_logger = logging.getLogger("email_logger")

    employee.set_password(temp_password)  # Set password directly on the Employee instance
    employee.is_active = True  # Activate the employee
    employee.save()  # Save the changes

    subject = "Welcome to the Company- Account Created"
    message = (
        f"Hello {employee.first_name},\n\n"
        f"Your account has been successfully created.\n\n"
        f"🔹 email: {employee.work_email}\n"
        f"🔹 Temporary Password: {temp_password}\n\n"
        f"Please login and reset your password immediately.\n\n"
        f"🔗 Employee Portal: http://127.0.0.1:8000/\n\n"
        f"Best Regards,\nHR Department\nS and S Steels"
    )
    print(f"📧 Sending welcome email to {employee.work_email} and password {temp_password}")

    try:
        send_mail(subject, message, settings.EMAIL_HOST_USER, [employee.work_email])
        email_logger.info(f"Welcome email sent successfully to {employee.work_email}")
    except Exception as e:
        email_logger.error(f"Failed to send email to {employee.work_email}: {e}")


@user_passes_test(is_hr_or_admin)
def employee_list(request):
    search_query = request.GET.get('search', '')
    department_filter = request.GET.get('department', '')
    sort_by = request.GET.get('sort', 'id')

    # Fetch active employees only
    employees = Employee.objects.select_related('department').filter(is_active=True)

    # Apply search filter
    if search_query:
        employees = employees.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(work_email__icontains=search_query)
        )

    # Apply department filter
    if department_filter:
        employees = employees.filter(department_id=department_filter)

    # Sorting options
    sort_options = {
        "id": "display_employee_id",
        "name": "first_name",
        "department": "department__name",
        "designation": "designation"
    }
    employees = employees.order_by(sort_options.get(sort_by, "id"))

    # Pagination
    paginator = Paginator(employees, 10)
    page_number = request.GET.get("page")
    employees_page = paginator.get_page(page_number)

    return render(request, 'employee/employee_list.html', {
        "employees": employees_page,
        "departments": Department.objects.all(),
    })



@user_passes_test(is_hr_or_admin)
def employee_detail(request, employee_id):
    # Use 'display_employee_id' field for querying the employee
    employee = get_object_or_404(Employee, id=employee_id)
    return render(request, 'employee/employee_detail.html', {'employee': employee})




@user_passes_test(is_hr_or_admin)
def employee_edit(request, employee_id):
    employee = get_object_or_404(Employee, display_employee_id=employee_id)
    
    if request.method == "POST":
        form = EmployeeForm(request.POST, instance=employee, is_edit=True)  # Pass is_edit=True
        if form.is_valid():
            form.save()
            messages.success(request, "Employee details updated successfully.", extra_tags="edit_success")
            return redirect("employee:employee_detail", employee_id=employee.id)
    else:
        form = EmployeeForm(instance=employee, is_edit=True)  # Pass is_edit=True here too

    return render(
        request,
        "employee/employee_form.html",
        {"form": form, "employee": employee, "action": "Edit"}
    )


@user_passes_test(is_hr_or_admin)
def inactive_employee_list(request):
    employees = Employee.objects.filter(is_active=False)

    return render(request, "employee/inactive_employee_list.html", {"employees": employees})


@user_passes_test(is_hr_or_admin)
def toggle_employee_status(request, employee_id):
    employee = get_object_or_404(Employee, display_employee_id=employee_id)
    
    # Toggle active/inactive status
    employee.is_active = not employee.is_active  
    employee.save(update_fields=['is_active'])

    # Show message
    if employee.is_active:
        messages.success(request, "Employee has been restored successfully.", extra_tags="restore_success")
    else:
        messages.success(request, "Employee has been deactivated.", extra_tags="delete_success")

    return redirect("employee:employee_list")
