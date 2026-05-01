import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'visitaPro.settings')
django.setup()

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from core.models import Visita, Empresa

group, created = Group.objects.get_or_create(name='Consultores')

ct_visita = ContentType.objects.get_for_model(Visita)
ct_empresa = ContentType.objects.get_for_model(Empresa)

perms = Permission.objects.filter(
    content_type__in=[ct_visita, ct_empresa], 
    codename__in=['view_empresa', 'add_visita', 'change_visita', 'view_visita']
)
group.permissions.set(perms)
print('Grupo Consultores criado com sucesso e permissoes aplicadas!')
