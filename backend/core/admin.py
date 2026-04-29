import json
import urllib.request
import urllib.parse
from django.contrib import admin, messages
from django.conf import settings
from .models import Contato, Disciplina, Regiao, Empresa, Visita, CustomUser

class EmpresaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'regiao', 'status', 'latitude', 'longitude')
    list_filter = ('regiao', 'status')
    search_fields = ('nome',)

def preview_cor(obj):
    return f'<span style="display:inline-block;width:20px;height:20px;border-radius:50%;background:{obj.cor_mapa};border:1px solid #ccc;"></span> {obj.cor_mapa}'
preview_cor.short_description = 'Cor no Mapa'
preview_cor.allow_tags = True

class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'first_name', 'last_name', 'email', 'is_consultor', 'is_admin', 'preview_cor_inline')
    list_filter = ('is_consultor', 'is_admin')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    fieldsets = (
        ('Dados de Acesso', {'fields': ('username', 'password')}),
        ('Informações Pessoais', {'fields': ('first_name', 'last_name', 'email', 'telefone', 'foto')}),
        ('Permissões', {'fields': ('is_consultor', 'is_admin', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Personalização do Mapa', {'fields': ('cor_mapa',), 'description': 'Escolha a cor dos pins das empresas deste consultor no mapa.'}),
    )

    def preview_cor_inline(self, obj):
        return f'<span style="display:inline-block;width:18px;height:18px;border-radius:50%;background:{obj.cor_mapa};border:1px solid #999;vertical-align:middle;"></span>'
    preview_cor_inline.short_description = 'Cor'
    preview_cor_inline.allow_tags = True

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Regiao)
admin.site.register(Empresa, EmpresaAdmin)
admin.site.register(Visita)
admin.site.register(Contato)
admin.site.register(Disciplina)
