"""
Serializers para a API de relatórios do VisitaPro.
"""

from rest_framework import serializers
from datetime import timedelta
from django.utils import timezone
from django.db.models import Count, Q, Sum, Avg
from django.db.models.functions import TruncDate, Coalesce
from .models import (
    Visita, Empresa, CustomUser, PerguntaRelatorio, 
    RespostaRelatorio, Jornada, VisitaFoto, Funcionario
)
from .relatorios_models import RelatorioGerado, ConfiguracaoRelatorio, TemplatePessoalizado


class ConfiguracaoRelatorioSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConfiguracaoRelatorio
        fields = [
            'id', 'ativa', 'periodo_relatorio_dias', 
            'enviar_email_automaticamente', 'frequencia_envio',
            'destinatarios_email', 'criado_em', 'atualizado_em'
        ]


class RelatorioGeradoSerializer(serializers.ModelSerializer):
    usuario_gerador_nome = serializers.CharField(
        source='usuario_gerador.get_full_name', 
        read_only=True
    )
    assessor_nome = serializers.CharField(
        source='assessor.get_full_name',
        read_only=True,
        allow_null=True
    )
    empresa_nome = serializers.CharField(
        source='empresa.nome',
        read_only=True,
        allow_null=True
    )

    class Meta:
        model = RelatorioGerado
        fields = [
            'id', 'titulo', 'tipo', 'formato', 'usuario_gerador',
            'usuario_gerador_nome', 'data_inicio', 'data_fim',
            'assessor', 'assessor_nome', 'empresa', 'empresa_nome',
            'arquivo', 'dados_json', 'criado_em', 'descricao'
        ]
        read_only_fields = [
            'id', 'usuario_gerador', 'criado_em', 'dados_json', 'arquivo'
        ]


class TemplatePessoalizadoSerializer(serializers.ModelSerializer):
    criador_nome = serializers.CharField(
        source='criador.get_full_name',
        read_only=True
    )

    class Meta:
        model = TemplatePessoalizado
        fields = [
            'id', 'nome', 'descricao', 'tipo_relatorio',
            'filtros_padrao', 'campos_incluir', 'ativo',
            'criador', 'criador_nome', 'criado_em', 'atualizado_em'
        ]
        read_only_fields = ['id', 'criador', 'criado_em', 'atualizado_em']


class ResumoGeralSerializer(serializers.Serializer):
    """Serializer para relatório de resumo geral"""
    
    total_visitas = serializers.IntegerField()
    visitas_realizadas = serializers.IntegerField()
    visitas_agendadas = serializers.IntegerField()
    visitas_canceladas = serializers.IntegerField()
    
    total_empresas = serializers.IntegerField()
    empresas_ativas = serializers.IntegerField()
    empresas_inativas = serializers.IntegerField()
    empresas_negociacao = serializers.IntegerField()
    
    taxa_conversao_percentual = serializers.FloatField()
    media_visitas_por_empresa = serializers.FloatField()
    
    total_assessores = serializers.IntegerField()
    distancia_media_percorrida = serializers.FloatField()
    
    periodo = serializers.DictField(child=serializers.CharField())


class PerformanceAssessorSerializer(serializers.Serializer):
    """Serializer para performance individual de assessor"""
    
    assessor_id = serializers.IntegerField()
    assessor_nome = serializers.CharField()
    
    total_visitas = serializers.IntegerField()
    visitas_realizadas = serializers.IntegerField()
    taxa_realizacao_percentual = serializers.FloatField()
    
    empresas_visitadas = serializers.IntegerField()
    empresas_ativas_assessor = serializers.IntegerField()
    
    distancia_total_km = serializers.FloatField()
    jornadas_trabalhadas = serializers.IntegerField()
    media_visitas_dia = serializers.FloatField()
    
    ultima_atividade = serializers.DateTimeField()


class StatusEmpresasSerializer(serializers.Serializer):
    """Serializer para status de empresas"""
    
    empresa_id = serializers.IntegerField()
    empresa_nome = serializers.CharField()
    status = serializers.CharField()
    
    assessor_responsavel = serializers.CharField(allow_null=True)
    total_visitas = serializers.IntegerField()
    ultima_visita = serializers.DateField(allow_null=True)
    
    funcionarios_total = serializers.IntegerField()
    data_conversao = serializers.DateField(allow_null=True)
    
    localizacao = serializers.DictField(child=serializers.CharField())


class VisitaDetalhadaSerializer(serializers.Serializer):
    """Serializer para visitas detalhadas com informações completas"""
    
    visita_id = serializers.IntegerField()
    empresa_nome = serializers.CharField()
    assessor_nome = serializers.CharField()
    
    data = serializers.DateField()
    horario = serializers.TimeField()
    status = serializers.CharField()
    
    duracao_minutes = serializers.IntegerField()
    funcionarios_atendidos = serializers.IntegerField()
    
    fotos_quantidade = serializers.IntegerField()
    respostas_formulario = serializers.ListField(child=serializers.DictField())
    
    observacoes = serializers.CharField(allow_blank=True)
    criado_em = serializers.DateTimeField()


class JornadaResumoSerializer(serializers.Serializer):
    """Serializer para resumo de jornadas"""
    
    jornada_id = serializers.IntegerField()
    assessor_nome = serializers.CharField()
    data = serializers.DateField()
    
    hora_inicio = serializers.TimeField()
    hora_fim = serializers.TimeField(allow_null=True)
    
    status = serializers.CharField()
    quilometragem_total = serializers.FloatField()
    visitas_realizadas = serializers.IntegerField()
    
    localizacao_inicio = serializers.DictField(child=serializers.CharField())
    localizacao_fim = serializers.DictField(child=serializers.CharField(), allow_null=True)


class ConversaoEmpresaSerializer(serializers.Serializer):
    """Serializer para análise de conversão de empresas"""
    
    empresa_id = serializers.IntegerField()
    empresa_nome = serializers.CharField()
    
    data_primeiro_contato = serializers.DateField()
    data_conversao = serializers.DateField(allow_null=True)
    
    dias_para_conversao = serializers.IntegerField(allow_null=True)
    visitas_pre_conversao = serializers.IntegerField()
    visitas_pos_conversao = serializers.IntegerField()
    
    status_atual = serializers.CharField()
    assessor_responsavel = serializers.CharField()


class FeedbackVisitaSerializer(serializers.Serializer):
    """Serializer para feedback e respostas de visitas"""
    
    visita_id = serializers.IntegerField()
    empresa_nome = serializers.CharField()
    data_visita = serializers.DateField()
    
    respostas = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField()
        )
    )
    observacoes = serializers.CharField(allow_blank=True)
    
    formulario_completo = serializers.BooleanField()
