# hr_portal/urls.py
from django.urls import path, include
from . import views

app_name = "hr_portal"

urlpatterns = [
    path('', views.universal_login, name='universal_login'),
    path('logout/', views.universal_logout, name='universal_logout'),

    path("dashboard/", views.hr_dashboard, name="hr_dashboard"),

    path("employee/", include(("employee.urls", 'employee_nested'), namespace='employee_nested')),
    path("department/", include(("department.urls", 'department_nested'), namespace='department_nested')),

    path('leave/', views.hr_leave_list, name='hr_leave_list'),
    path('leave/approve/<int:pk>/', views.hr_leave_approve, name='hr_leave_approve'),
    path('leave/reject/<int:pk>/', views.hr_leave_reject, name='hr_leave_reject'),

    
    
    
    ]