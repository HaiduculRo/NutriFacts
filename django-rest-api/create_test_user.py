import os

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User


def create_test_user():
    try:
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            is_active=True
        )
        print(f"Test user created successfully: {user.email}")
    except Exception as e:
        print(f"Error creating test user: {e}")

if __name__ == '__main__':
    create_test_user() 