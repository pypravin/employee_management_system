import os
import shutil
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Employee

@receiver(post_delete, sender=Employee)
def handle_employee_deletion(sender, instance, **kwargs):
   
    # 🔹 Delete the associated User instance
    try:
        user = User.objects.get(username=instance.display_employee_id)
        user.delete()
        print(f"✅ User {instance.display_employee_id} deleted successfully.")
    except User.DoesNotExist:
        print(f"⚠️ User {instance.display_employee_id} not found. No deletion needed.")

    # 🔹 Delete the facial data folder
    folder_path = f"D:/soft_proj/employee_management_system/media/facial_data/{instance.id}"
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)
        print(f"✅ Deleted facial data for {instance.id}")
    else:
        print(f"⚠️ No facial data found for {instance.id}. Nothing to delete.")
