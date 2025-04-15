from django.contrib import admin
from django.urls import path
from django.urls.conf import include
from django.contrib.auth import views as auth_views
from accounts.forms import CustomPasswordResetForm
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("hr_portal.urls")),
    path("employee/", include("employee.urls")),
    path("employee_portal/", include("employee_portal.urls")),
    path("department/", include("department.urls")),
    path("leaves/", include("leaves.urls")),
    path("notifications/", include("notifications.urls")),
    path("attendance/", include("attendance.urls")),
    path("report/", include("report.urls")),
    path('accounts/password_reset/', auth_views.PasswordResetView.as_view(form_class=CustomPasswordResetForm), name='password_reset'),
    path('accounts/', include('django.contrib.auth.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = 'hr_portal.views.custom_404'
handler500 = 'hr_portal.views.custom_500'
handler403 = 'hr_portal.views.custom_403'