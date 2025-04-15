from django import forms
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.template.loader import render_to_string
from django.core.mail import send_mail

User = get_user_model()

class CustomPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(
        label="Work Email",
        max_length=254,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )

    def get_users(self, email):
        """Override get_users to match by 'work_email' instead of 'email'."""
        return User.objects.filter(work_email__iexact=email, is_active=True)

    def save(self, request, domain_override=None,
             subject_template_name="registration/password_reset_subject.txt",
             email_template_name="registration/password_reset_email.html",
             use_https=False, token_generator=default_token_generator,
             from_email=None, html_email_template_name=None,
             extra_email_context=None):  # ✅ Add `extra_email_context`
        """
        Generates a one-use only link for resetting password.
        Sends an email with the reset link.
        """
        email = self.cleaned_data["email"]
        active_users = self.get_users(email)
        for user in active_users:
            domain = domain_override or request.get_host()
            protocol = "https" if use_https else "http"

            context = {
                "email": user.work_email,  # Use work_email instead of email
                "domain": domain,
                "site_name": "Employee Management System",
                "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                "user": user,
                "token": token_generator.make_token(user),
                "protocol": protocol,
            }

            # ✅ Merge `extra_email_context` into `context` if provided
            if extra_email_context:
                context.update(extra_email_context)

            message = render_to_string(email_template_name, context)
            send_mail(
                subject=render_to_string(subject_template_name, context).strip(),
                message=message,
                from_email=from_email,
                recipient_list=[user.work_email],  # Use work_email instead of email
                html_message=render_to_string(html_email_template_name, context) if html_email_template_name else None,
            )
