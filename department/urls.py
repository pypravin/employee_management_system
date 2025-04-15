from django.urls import path
from . import views

app_name = "department"

urlpatterns = [
    path("", views.department_list, name="department_list"),
    path("create/", views.department_create, name="department_create"),
    path("update/<int:pk>/", views.department_update, name="department_update"),
    path("delete/<int:pk>/", views.department_delete, name="department_delete"),
    path('deactivate/<int:department_id>/', views.deactivate_department, name='deactivate_department'),
    path('reactivate/<int:pk>/', views.reactivate_department, name='reactivate_department'),
    path('archived/', views.archived_departments, name='archived_departments'),
]
