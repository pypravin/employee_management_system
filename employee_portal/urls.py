from . import views
from django.urls import path
from django.contrib.auth import views as auth_views

app_name = "employee_portal"

urlpatterns = [
    path('', views.universal_login, name='universal_login'),
    path('logout/', views.universal_logout, name='universal_logout'),

    path('change-password/', views.ForcePasswordChangeView.as_view(), name='force_password_change'),
    path('dashboard/', views.employee_dashboard, name='employee_dashboard'),
    path('profile/', views.employee_profile, name='employee_profile'),

    # password reseting
    path("password_reset/", auth_views.PasswordResetView.as_view(), name="password_reset"),
    path("password_reset/done/", auth_views.PasswordResetDoneView.as_view(), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("reset/done/", auth_views.PasswordResetCompleteView.as_view(), name="password_reset_complete"),

]