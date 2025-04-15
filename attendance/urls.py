from django.urls import path
from .views import (
    manual_attendance, 
    search_employee, 
    record_attendance, 
    start_face_recognition, 
    attendance_page,
    get_employee_attendance,
    attendance_list,
    get_attendance_details,
    get_latest_attendance,
    train_facial_model_view,
    employee_attendance_history,
    absent_list


)

app_name = "attendance"

urlpatterns = [
    # Manual Attendance URLs
    path("manual/", manual_attendance, name="manual_attendance"),
    path("search/", search_employee, name="search_employee"),
    path("record/", record_attendance, name="record_attendance"),
    path("get_employee_attendance/", get_employee_attendance, name="get_employee_attendance"),
    path("attendance_list/", attendance_list, name="attendance_list"),
    path("get_attendance_details/<int:id>/", get_attendance_details, name="get_attendance_details"),
    path("get_latest_attendance/", get_latest_attendance, name="get_latest_attendance"),

    # Facial Recognition URLs
    path("trigger-face-recognition/", start_face_recognition, name="trigger_face_recognition"),
    path("face-attendance/", attendance_page, name="face_attendance"),
    path("train-facial-model/", train_facial_model_view, name="train_facial_model"),

    # employee attendance history
    path('attendance/history/', employee_attendance_history, name='employee_attendance_history'),

    path('absent/', absent_list, name='absent_list'),

]
