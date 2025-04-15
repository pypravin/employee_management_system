import cv2
import numpy as np
import os
from django.conf import settings
from employee.models import Employee
from django.core.management.base import BaseCommand
class Command(BaseCommand):
    help = 'Trains the facial recognition model'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting model training...'))
        data_dir = os.path.join(settings.MEDIA_ROOT, "facial_data")
        recognizer = cv2.face.LBPHFaceRecognizer_create()
        faces =[]
        labels =[]

        employee_ids =[]
        for employee in Employee.objects.all():
            if employee.display_employee_id not in employee_ids:
                employee_ids.append(employee.display_employee_id)

        label_map = {emp_id: i for i, emp_id in enumerate(employee_ids)}

        for emp_id in os.listdir(data_dir):
            employee_path = os.path.join(data_dir, emp_id)
            if os.path.isdir(employee_path):
                label = label_map.get(emp_id)
                if label is not None:
                    for filename in os.listdir(employee_path):
                        if filename.endswith(".jpg"):
                            image_path = os.path.join(employee_path, filename)
                            img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
                            if img is not None:
                                resized_img = cv2.resize(img, (100, 100)) 
                                faces.append(resized_img)
                                labels.append(label)
        if faces:
            self.stdout.write(f"Training on {len(faces)} images...")
            recognizer.train(faces, np.array(labels))
            model_path = os.path.join(settings.BASE_DIR, 'trained_model.yml')
            recognizer.save(model_path)
            self.stdout.write(self.style.SUCCESS(f"Model trained and saved to {model_path}"))
        else:
            self.stdout.write(self.style.WARNING("No facial data found for training."))