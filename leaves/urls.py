from django.urls import path
from . import views

app_name = "leaves"

urlpatterns = [
    path("apply/", views.LeaveRequestCreateView.as_view(), name="apply_leave"),
    path("history/", views.LeaveRequestListView.as_view(), name="leave_history"),
    path("update/<int:pk>/", views.LeaveRequestUpdateView.as_view(), name="update_leave"),
    path("cancel/<int:pk>/", views.cancel_leave, name="cancel_leave"),
]