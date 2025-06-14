# Generated by Django 5.1.6 on 2025-02-14 06:49

import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("department", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Employee",
            fields=[
                ("password", models.CharField(max_length=128, verbose_name="password")),
                (
                    "last_login",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="last login"
                    ),
                ),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "display_employee_id",
                    models.CharField(
                        editable=False, max_length=10, null=True, unique=True
                    ),
                ),
                ("first_name", models.CharField(max_length=50)),
                ("last_name", models.CharField(max_length=50)),
                ("designation", models.CharField(max_length=50)),
                ("hire_date", models.DateField(blank=True, null=True)),
                ("work_email", models.EmailField(max_length=254, unique=True)),
                ("facial_enrollment_status", models.BooleanField(default=False)),
                ("first_login", models.BooleanField(default=True)),
                ("is_active", models.BooleanField(default=True)),
                ("is_hr", models.BooleanField(default=False)),
                ("is_staff", models.BooleanField(default=False)),
                ("is_superuser", models.BooleanField(default=False)),
                (
                    "department",
                    models.ForeignKey(
                        db_column="department_id",
                        db_constraint=False,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="department.department",
                    ),
                ),
                (
                    "groups",
                    models.ManyToManyField(
                        blank=True,
                        help_text="The groups this user belongs to. A user will get all permissions granted to each of their groups.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.group",
                        verbose_name="groups",
                    ),
                ),
                (
                    "user_permissions",
                    models.ManyToManyField(
                        blank=True,
                        help_text="Specific permissions for this user.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.permission",
                        verbose_name="user permissions",
                    ),
                ),
            ],
            options={
                "verbose_name": "Employee",
                "verbose_name_plural": "Employees",
            },
        ),
    ]
