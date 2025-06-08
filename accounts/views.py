from django.shortcuts import render, redirect
from .forms import CustomPasswordResetForm
from django.contrib.auth.views import PasswordResetView

class CustomPasswordResetView(PasswordResetView):
    form_class = CustomPasswordResetForm
    template_name = 'registration/password_reset_form.html'  # Replace with your template path
    email_template_name = 'registration/password_reset_email.html'
    subject_template_name = 'registration/password_reset_subject.txt'
    success_url = '/accounts/password_reset/done'  # Replace with your success URL


def password_reset(request):
    if request.method == 'POST':
        form = CustomPasswordResetForm(request.POST, request=request)  # Pass request here
        if form.is_valid():
            form.save() #No need to pass the request here
            return redirect('password_reset_done')  # Redirect to the 'password_reset_done' URL
    else:
        form = CustomPasswordResetForm(request=request)  # Pass request here for get request
    return render(request, 'registration/password_reset_form.html', {'form': form})