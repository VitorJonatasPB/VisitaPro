"""
Modelos para o sistema de relatórios do VisitaPro.
Mantém histórico de relatórios gerados e configurações de relatórios.
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings


class ConfiguracaoRelatorio(models.Model):
    """Configurações globais para relatórios"""
    
    ativa = models.BooleanField(default=True)
    periodo_relatorio_dias = models.IntegerField(
        default=30,
        help_text="Período padrão para relatórios em dias"
    )
    enviar_email_automaticamente = models.BooleanField(
        default=False,
        help_text="Enviar relatórios automaticamente via email"
    )
    frequencia_envio = models.CharField(
        max_length=20,
        choices=[
            ('diario', 'Diário'),
            ('semanal', 'Semanal'),
            ('mensal', 'Mensal'),
        ],
        default='mensal'
    )
    destinatarios_email = models.TextField(
        blank=True,
        null=True,
        help_text="Emails separados por vírgula"
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuração de Relatório"
        verbose_name_plural = "Configurações de Relatório"

    def __str__(self):
        return f"Configuração de Relatório - Período: {self.periodo_relatorio_dias} dias"


class RelatorioGerado(models.Model):
    """Histórico de relatórios gerados"""
    
    TIPO_CHOICES = [
        ('resumo_geral', 'Resumo Geral'),
        ('performance_assessor', 'Performance do Assessor'),
        ('status_empresas', 'Status de Empresas'),
        ('conversoes', 'Taxa de Conversão'),
        ('visitas_detalhadas', 'Visitas Detalhadas'),
        ('jornadas', 'Jornadas e Quilometragem'),
        ('feedback_visitas', 'Feedback das Visitas'),
        ('comparativo_periodo', 'Comparativo de Períodos'),
    ]

    FORMATO_CHOICES = [
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('json', 'JSON'),
        ('html', 'HTML'),
    ]

    titulo = models.CharField(max_length=200)
    tipo = models.CharField(max_length=30, choices=TIPO_CHOICES)
    formato = models.CharField(max_length=10, choices=FORMATO_CHOICES, default='pdf')
    
    usuario_gerador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='relatorios_gerados'
    )
    
    # Filtros aplicados
    data_inicio = models.DateField(null=True, blank=True)
    data_fim = models.DateField(null=True, blank=True)
    assessor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='relatorios_sobre'
    )
    empresa = models.ForeignKey(
        'Empresa',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='relatorios_gerados'
    )
    
    # Arquivo gerado
    arquivo = models.FileField(
        upload_to='relatorios/',
        blank=True,
        null=True
    )
    
    # Dados JSON para visualização rápida
    dados_json = models.JSONField(default=dict, blank=True)
    
    criado_em = models.DateTimeField(auto_now_add=True)
    descricao = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-criado_em']
        verbose_name = "Relatório Gerado"
        verbose_name_plural = "Relatórios Gerados"
        indexes = [
            models.Index(fields=['-criado_em']),
            models.Index(fields=['tipo', '-criado_em']),
            models.Index(fields=['usuario_gerador', '-criado_em']),
        ]

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.criado_em.strftime('%d/%m/%Y')}"


class TemplatePessoalizado(models.Model):
    """Templates personalizados para relatórios por usuário/empresa"""
    
    nome = models.CharField(max_length=150)
    descricao = models.TextField(blank=True, null=True)
    tipo_relatorio = models.CharField(
        max_length=30,
        choices=RelatorioGerado.TIPO_CHOICES
    )
    
    # Filtros padrão
    filtros_padrao = models.JSONField(default=dict)
    
    # Configuração de campos a incluir
    campos_incluir = models.JSONField(
        default=list,
        help_text="Lista de campos a incluir no relatório"
    )
    
    ativo = models.BooleanField(default=True)
    criador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='templates_relatorios'
    )
    
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Template Personalizado"
        verbose_name_plural = "Templates Personalizados"
        unique_together = ('nome', 'criador')

    def __str__(self):
        return f"{self.nome} ({self.criador.username})"
