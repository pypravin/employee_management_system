from django.urls import path
from . import views

app_name = "employee"

urlpatterns = [
    path("register/", views.register_employee, name="register_employee"),
    path("list/", views.employee_list, name="employee_list"),
    path("register_facial/<str:employee_id>/", views.register_facial, name="register_facial"),
    path("capture_face/<str:employee_id>/", views.capture_face, name="capture_face"),
    path("detail/<str:employee_id>/", views.employee_detail, name="employee_detail"),
    path("edit/<str:employee_id>/", views.employee_edit, name="employee_edit"),  
    path("inactive/", views.inactive_employee_list, name="inactive_employee_list"),
    path("no-access/", views.no_access, name="no_access"),
    
    # 🔄 Replace delete & restore with a single toggle view
    path("<str:employee_id>/toggle-status/", views.toggle_employee_status, name="toggle_employee_status"),
]
