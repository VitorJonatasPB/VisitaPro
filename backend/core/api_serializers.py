from rest_framework import serializers
from django.utils import timezone
from .models import Visita, PerguntaRelatorio, RespostaRelatorio, VisitaFoto, CustomUser, BugReport, Professor, Escola


class VisitaAgendaSerializer(serializers.ModelSerializer):
    """Serializer resumido para exibição na Agenda do consultor."""
    escola_nome = serializers.ReadOnlyField(source='escola.nome')
    escola_lat = serializers.ReadOnlyField(source='escola.latitude')
    escola_lng = serializers.ReadOnlyField(source='escola.longitude')

    class Meta:
        model = Visita
        fields = [
            'id', 'escola_nome', 'escola_lat', 'escola_lng', 'data', 'horario', 'status',
            'checkin_time', 'checkout_time',
        ]


class EscolaSerializer(serializers.ModelSerializer):
    regiao_nome = serializers.ReadOnlyField(source='regiao.nome')

    class Meta:
        model = Escola
        fields = [
            'id', 'nome', 'regiao_nome', 'telefone', 'email', 
            'status', 'frequencia_recomendada_dias', 'ultima_visita',
            'latitude', 'longitude'
        ]


class VisitaDetalheSerializer(serializers.ModelSerializer):
    """Serializer detalhado com as informações completas da Escola."""
    escola = EscolaSerializer(read_only=True)
    escola_nome = serializers.ReadOnlyField(source='escola.nome')

    class Meta:
        model = Visita
        fields = [
            'id', 'escola', 'escola_nome', 'data', 'horario', 'status',
            'checkin_time', 'checkout_time', 'observacoes'
        ]


class PerguntaRelatorioSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerguntaRelatorio
        fields = ['id', 'texto', 'tipo_resposta', 'opcoes_resposta', 'fonte_dados']


class RespostaRelatorioSerializer(serializers.ModelSerializer):
    class Meta:
        model = RespostaRelatorio
        fields = ['pergunta', 'resposta']


class CheckinSerializer(serializers.Serializer):
    checkin_lat = serializers.CharField(required=True)
    checkin_lng = serializers.CharField(required=True)
    checkin_time = serializers.DateTimeField(required=False, default=timezone.now)
    justificativa_distancia = serializers.CharField(required=False, allow_blank=True, default='')


class CheckoutSerializer(serializers.Serializer):
    checkout_lat = serializers.CharField(required=True)
    checkout_lng = serializers.CharField(required=True)
    checkout_time = serializers.DateTimeField(required=False, default=timezone.now)


class RelatorioPayloadSerializer(serializers.Serializer):
    respostas = RespostaRelatorioSerializer(many=True, required=False)
    assinatura = serializers.CharField(required=False, allow_blank=True)
    professores_atendidos = serializers.ListField(
        child=serializers.IntegerField(), required=False
    )


class ProfessorSerializer(serializers.ModelSerializer):
    escola_nome = serializers.ReadOnlyField(source='escola.nome')
    class Meta:
        model = Professor
        fields = ['id', 'nome', 'matricula', 'escola_nome', 'telefone', 'email']


class VisitaFotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = VisitaFoto
        fields = ['id', 'imagem', 'data_upload']


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'telefone', 'foto']
        read_only_fields = ['id', 'username', 'email']


class BugReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = BugReport
        fields = ['id', 'descricao', 'device_info', 'criado_em', 'resolvido']
        read_only_fields = ['id', 'criado_em', 'resolvido']
