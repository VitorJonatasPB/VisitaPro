"""
Configuração do Django Admin para o módulo de relatórios.
Adicionar isto ao admin.py existente.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .relatorios_models import (
    ConfiguracaoRelatorio,
    RelatorioGerado,
    TemplatePessoalizado
)


@admin.register(ConfiguracaoRelatorio)
class ConfiguracaoRelatorioAdmin(admin.ModelAdmin):
    list_display = [
        'ativa',
        'periodo_relatorio_dias',
        'frequencia_envio',
        'enviar_email_automaticamente'
    ]
    
    fieldsets = (
        ('Status', {
            'fields': ('ativa',)
        }),
        ('Configuração de Período', {
            'fields': ('periodo_relatorio_dias',)
        }),
        ('Envio Automático', {
            'fields': (
                'enviar_email_automaticamente',
                'frequencia_envio',
                'destinatarios_email'
            ),
            'description': 'Configure para enviar relatórios automaticamente'
        }),
        ('Metadata', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ('criado_em', 'atualizado_em')

    def has_add_permission(self, request):
        # Apenas uma configuração deve existir
        return not ConfiguracaoRelatorio.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(RelatorioGerado)
class RelatorioGeradoAdmin(admin.ModelAdmin):
    list_display = [
        'titulo_link',
        'tipo_badge',
        'formato_badge',
        'usuario_gerador',
        'periodo_display',
        'criado_em_display',
        'arquivo_link'
    ]
    
    list_filter = [
        'tipo',
        'formato',
        'criado_em',
        ('data_inicio', admin.SimpleListFilter),
        'usuario_gerador'
    ]
    
    search_fields = [
        'titulo',
        'usuario_gerador__username',
        'empresa__nome',
        'assessor__username'
    ]
    
    readonly_fields = [
        'usuario_gerador',
        'criado_em',
        'dados_json_display'
    ]
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('titulo', 'tipo', 'formato')
        }),
        ('Filtros Aplicados', {
            'fields': (
                'usuario_gerador',
                'data_inicio',
                'data_fim',
                'assessor',
                'empresa'
            )
        }),
        ('Arquivo e Dados', {
            'fields': (
                'arquivo',
                'dados_json_display'
            )
        }),
        ('Metadata', {
            'fields': ('criado_em', 'descricao'),
            'classes': ('collapse',)
        })
    )
    
    ordering = ['-criado_em']
    
    def titulo_link(self, obj):
        """Mostra o título como um link clicável"""
        url = reverse('admin:core_relatoriogerad_change', args=[obj.id])
        return format_html('<a href="{}">{}</a>', url, obj.titulo)
    titulo_link.short_description = 'Título'
    
    def tipo_badge(self, obj):
        """Mostra o tipo em uma badge colorida"""
        cores = {
            'resumo_geral': '#0D6EFD',
            'performance_assessor': '#198754',
            'status_empresas': '#0DCAF0',
            'visitas_detalhadas': '#FFC107',
            'jornadas': '#6C757D',
            'conversoes': '#E91E63',
            'feedback_visitas': '#9C27B0',
        }
        cor = cores.get(obj.tipo, '#6C757D')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; '
            'border-radius: 4px; font-size: 12px;">{}</span>',
            cor,
            obj.get_tipo_display()
        )
    tipo_badge.short_description = 'Tipo'
    
    def formato_badge(self, obj):
        """Mostra o formato em uma badge"""
        return format_html(
            '<span style="background-color: #6C757D; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            obj.formato.upper()
        )
    formato_badge.short_description = 'Formato'
    
    def periodo_display(self, obj):
        """Mostra o período de forma legível"""
        if obj.data_inicio and obj.data_fim:
            dias = (obj.data_fim - obj.data_inicio).days + 1
            return f'{obj.data_inicio.strftime("%d/%m/%Y")} a {obj.data_fim.strftime("%d/%m/%Y")} ({dias}d)'
        return '-'
    periodo_display.short_description = 'Período'
    
    def criado_em_display(self, obj):
        """Mostra data/hora em formato legível"""
        return obj.criado_em.strftime('%d/%m/%Y %H:%M')
    criado_em_display.short_description = 'Gerado em'
    
    def arquivo_link(self, obj):
        """Mostra link para download se arquivo existe"""
        if obj.arquivo:
            return format_html(
                '<a href="{}" class="button" target="_blank">📥 Download</a>',
                obj.arquivo.url
            )
        return '—'
    arquivo_link.short_description = 'Arquivo'
    
    def dados_json_display(self, obj):
        """Mostra preview dos dados JSON"""
        import json
        try:
            dados = json.dumps(obj.dados_json, indent=2, ensure_ascii=False)
            return format_html(
                '<pre style="max-height: 400px; overflow-y: auto; '
                'background-color: #f5f5f5; padding: 10px; border-radius: 4px;">{}</pre>',
                dados
            )
        except:
            return 'Erro ao exibir dados'
    dados_json_display.short_description = 'Preview dos Dados (JSON)'
    
    def has_add_permission(self, request):
        # Relatórios devem ser criados via endpoints específicos
        return False
    
    def has_change_permission(self, request, obj=None):
        # Não permitir editar relatórios gerados
        return False
    
    actions = ['deletar_relatorios_antigos']
    
    def deletar_relatorios_antigos(self, request, queryset):
        """Action para deletar relatórios selecionados"""
        count = queryset.count()
        queryset.delete()
        self.message_user(
            request,
            f'✓ {count} relatório(s) deletado(s) com sucesso'
        )
    deletar_relatorios_antigos.short_description = 'Deletar relatórios selecionados'


@admin.register(TemplatePessoalizado)
class TemplatePessoalizadoAdmin(admin.ModelAdmin):
    list_display = [
        'nome',
        'tipo_relatorio',
        'criador',
        'ativo_badge',
        'criado_em'
    ]
    
    list_filter = [
        'tipo_relatorio',
        'ativo',
        'criado_em',
        'criador'
    ]
    
    search_fields = [
        'nome',
        'descricao',
        'criador__username'
    ]
    
    readonly_fields = [
        'criador',
        'criado_em',
        'atualizado_em',
        'filtros_padrao_display',
        'campos_incluir_display'
    ]
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': (
                'nome',
                'descricao',
                'tipo_relatorio',
                'ativo'
            )
        }),
        ('Configuração', {
            'fields': (
                'filtros_padrao_display',
                'campos_incluir_display'
            )
        }),
        ('Criador', {
            'fields': ('criador',)
        }),
        ('Metadata', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        })
    )
    
    def ativo_badge(self, obj):
        """Mostra status ativo em uma badge"""
        if obj.ativo:
            return format_html(
                '<span style="background-color: #198754; color: white; '
                'padding: 3px 8px; border-radius: 3px;">✓ Ativo</span>'
            )
        return format_html(
            '<span style="background-color: #6C757D; color: white; '
            'padding: 3px 8px; border-radius: 3px;">✗ Inativo</span>'
        )
    ativo_badge.short_description = 'Status'
    
    def filtros_padrao_display(self, obj):
        """Exibe filtros padrão"""
        import json
        return format_html(
            '<pre style="background-color: #f5f5f5; padding: 10px; '
            'border-radius: 4px;">{}</pre>',
            json.dumps(obj.filtros_padrao, indent=2)
        )
    filtros_padrao_display.short_description = 'Filtros Padrão'
    
    def campos_incluir_display(self, obj):
        """Exibe campos a incluir"""
        campos = ', '.join(obj.campos_incluir) if obj.campos_incluir else 'Nenhum'
        return format_html(
            '<p>{}</p>',
            campos
        )
    campos_incluir_display.short_description = 'Campos a Incluir'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_staff:
            return qs.filter(criador=request.user)
        return qs
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.criador = request.user
        super().save_model(request, obj, form, change)
