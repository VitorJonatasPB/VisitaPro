import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'visitas_escolares.settings')
django.setup()

from core.models import CustomUser

if not CustomUser.objects.filter(username='admin').exists():
    user = CustomUser.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    user.is_admin = True
    user.save()
    print("Superuser 'admin' created with password 'admin123'")
else:
    print("Superuser 'admin' already exists")
