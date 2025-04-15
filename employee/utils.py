from django.contrib.auth.hashers import make_password
import random
import string

def generate_temp_password():
    """Generate a random password and return plain versions."""
    temp_password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    return temp_password, 
