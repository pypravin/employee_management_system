import cv2
import os
import sys
import pickle
from pathlib import Path
import django
from datetime import datetime, timedelta
from django.utils.timezone import localtime, now
from django.conf import settings
import numpy as np
import time
# Setup Django environment
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "employee_management_system.settings")
django.setup()

from employee.models import Employee
from attendance.models import Attendance
from leaves.utils import is_employee_on_leave

# Initialize Haar cascade for face detection
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

# Initialize webcam
video_capture = cv2.VideoCapture(0)

if not video_capture.isOpened():
    print("Error: Could not access webcam.")
    sys.exit()

# Set video capture frame size
video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

print("Starting real-time face recognition... Press 'Q' to quit.")

def load_trained_model():
    """Load the trained LBPH model."""
    model_path = os.path.join(settings.BASE_DIR, 'trained_model.yml')
    if os.path.exists(model_path):
        recognizer = cv2.face.LBPHFaceRecognizer_create()
        recognizer.read(model_path)
        return recognizer
    else:
        print(f"Error: Trained model not found at {model_path}")
        return None

# Load the trained model
lbph_recognizer = load_trained_model()

if lbph_recognizer is None:
    sys.exit()

# Cooldown period to prevent duplicate attendance
COOLDOWN_PERIOD = timedelta(minutes=5)
last_recognized_time = {}

# Variables for recognition hold and skip
last_recognition_time_visual = None
recognition_hold_duration = 5  # Extend the hold duration
recognized_face_id = None  # To store the ID of the recognized employee
skip_recognition_duration = 3 # seconds to skip recognition after successful recognition
last_skip_recognition_time = None

while True:
    ret, frame = video_capture.read()
    if not ret:
        print("Error capturing video.")
        break

    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray_frame, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
    print(f"Faces found: {len(faces)}")

    employee_id_mapping = {}
    all_employees = Employee.objects.all()
    for i, employee in enumerate(all_employees):
        employee_id_mapping[i] = employee.display_employee_id

    current_time_visual = time.time()

    for (x, y, w, h) in faces:
        confidence = 1.0
        name = "Unknown"
        color = (0, 0, 255)  # Default to red

        # Check if we should skip recognition for this face
        if last_skip_recognition_time and (current_time_visual - last_skip_recognition_time) < skip_recognition_duration and recognized_face_id is not None:
            try:
                employee = Employee.objects.get(display_employee_id=recognized_face_id)
                name = employee.full_name
                color = (0, 255, 0) # Keep it green
                print(f"Skipping recognition for recently recognized: {name}")
            except Employee.DoesNotExist:
                recognized_face_id = None # Reset if employee not found
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            cv2.putText(frame, f"{name}", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            continue # Move to the next face

        if lbph_recognizer:
            face_img = gray_frame[y:y + h, x:x + w]
            resized_face = cv2.resize(face_img, (100, 100))
            label, confidence = lbph_recognizer.predict(resized_face)
            print(f"Predicted Label: {label}, Confidence: {confidence}")
            recognized_employee_display_id = employee_id_mapping.get(label)

            print(f"Confidence before check: {confidence:.2f}")
            if recognized_employee_display_id and confidence < 80:
                print(f"Recognized Employee ID from mapping: {recognized_employee_display_id}")
                try:
                    employee = Employee.objects.get(display_employee_id=recognized_employee_display_id)
                    name = employee.full_name

                    if is_employee_on_leave(employee):
                        color = (0, 165, 255)  # Orange color for employee on leave
                        print(f"{name} is on leave.")
                    else:
                        color = (0, 255, 0) # Green color for recognized employee
                        last_recognition_time_visual = current_time_visual
                        recognized_face_id = employee.display_employee_id # Store the recognized display ID

                        current_time = localtime(now())
                        last_time = last_recognized_time.get(employee.id)

                        if last_time and (current_time - last_time) < COOLDOWN_PERIOD:
                            print(f"{name} was recognized recently. Skipping attendance.")
                            continue

                        last_recognized_time[employee.id] = current_time

                        today = now().date()
                        existing_attendance = Attendance.objects.filter(employee=employee, date=today).first()

                        if not existing_attendance:
                            Attendance.objects.create(
                                employee=employee,
                                date=today,
                                time_in=current_time.time(),
                                method="Facial Recognition"
                            )
                            print(f"Time In recorded for {name} at {current_time}")
                            print(f"Recognized Employee ID: {employee.id}")
                            last_skip_recognition_time = current_time_visual # Start the skip timer
                            # break # Optionally break the loop after successful recognition and logging
                            # sys.exit() # Optionally exit the script after successful recognition and logging
                        elif existing_attendance.time_in and not existing_attendance.time_out:
                            existing_attendance.time_out = current_time.time()
                            existing_attendance.save()
                            print(f"Time Out recorded for {name} at {current_time}")
                            print(f"Recognized Employee ID: {employee.id}")
                            last_skip_recognition_time = current_time_visual # Start the skip timer
                            # break # Optionally break the loop after successful recognition and logging
                            # sys.exit() # Optionally exit the script after successful recognition and logging
                        else:
                            print(f"{name} already has Time In and Time Out recorded today.")
                            print(f"Recognized Employee ID: {employee.id}")
                            last_skip_recognition_time = current_time_visual # Start the skip timer
                            # break # Optionally break the loop if you want to redirect even if already marked
                            # sys.exit() # Optionally exit the script

                except Employee.DoesNotExist:
                    print(f"Employee with ID {recognized_employee_display_id} not found.")
                    name = "Unknown"
                    color = (0, 0, 255)

        # Keep the box green (or orange if on leave) for a duration after successful recognition
        elif last_recognition_time_visual and (current_time_visual - last_recognition_time_visual) < recognition_hold_duration and recognized_face_id is not None:
            try:
                employee = Employee.objects.get(display_employee_id=recognized_face_id)
                name = employee.full_name
                if is_employee_on_leave(employee):
                    color = (0, 165, 255)  # Orange color for employee on leave
                else:
                    color = (0, 255, 0)
            except Employee.DoesNotExist:
                recognized_face_id = None # Reset if employee not found

        print(f"Color: {color}")

        cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
        cv2.putText(frame, f"{name}", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

    cv2.putText(frame, f"Faces detected: {len(faces)}", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    cv2.imshow("Face Recognition Attendance", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

video_capture.release()
cv2.destroyAllWindows()
print("Face recognition stopped.")
sys.exit()