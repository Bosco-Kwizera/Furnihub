#!/usr/bin/env python
import os
import sys
import django
from pathlib import Path

# Add the project directories to Python path
parent_dir = Path(__file__).parent
project_dir = parent_dir / 'furnihub'
sys.path.insert(0, str(parent_dir))
sys.path.insert(0, str(project_dir))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'furnihub.settings')
django.setup()

from django.contrib.auth.models import User

# Create superuser
try:
    if not User.objects.filter(username='admin').exists():
        user = User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
        print(f"✓ Superuser created successfully!")
        print(f"  Username: admin")
        print(f"  Email: admin@example.com")
        print(f"  Password: admin123")
    else:
        print("✓ Superuser 'admin' already exists")
        user = User.objects.get(username='admin')
        user.set_password('admin123')
        user.save()
        print(f"  Password reset to: admin123")
except Exception as e:
    print(f"✗ Error creating superuser: {e}")
    sys.exit(1)
