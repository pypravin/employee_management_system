from django.urls import path
from . import views

app_name = "report"

urlpatterns = [
    path('dashboard/', views.report_dashboard, name='report_dashboard'),
    path('employee/', views.employee_report, name='employee_report'),
    path('employee/export/', views.employee_report_export, name='employee_report_export'),
    path('employee/<uuid:id>/', views.employee_report_detail, name='employee_report_detail'),
    path('employee_report/export/<str:format>/', views.employee_report_export, name='employee_report_export'),    
    path('attendance/', views.attendance_report, name='attendance_report'),
    path('department/', views.department_report, name='department_report'),
    path('late_comer/', views.late_comer_report, name='late_comer_report'),
    path('performance/', views.performance_report, name='performance_report'),
]
