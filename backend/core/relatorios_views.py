"""
Views (API endpoints) para o sistema de relatórios.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import JSONParser
from django.db.models import Count, Q
from django.utils import timezone
from django.http import FileResponse, HttpResponse
from django.shortcuts import get_object_or_404
from datetime import datetime, timedelta
import json

from .models import Visita, Empresa, CustomUser
from .relatorios_models import RelatorioGerado, ConfiguracaoRelatorio, TemplatePessoalizado
from .relatorios_serializers import (
    RelatorioGeradoSerializer,
    ConfiguracaoRelatorioSerializer,
    TemplatePessoalizadoSerializer,
    ResumoGeralSerializer,
    PerformanceAssessorSerializer,
    StatusEmpresasSerializer,
    VisitaDetalhadaSerializer,
    JornadaResumoSerializer,
    ConversaoEmpresaSerializer,
    FeedbackVisitaSerializer
)
from .relatorios_utils import GeradorRelatorios, ExportadorRelatorios


class ConfiguracaoRelatorioViewSet(viewsets.ModelViewSet):
    """ViewSet para gerenciar configurações de relatórios"""
    
    queryset = ConfiguracaoRelatorio.objects.all()
    serializer_class = ConfiguracaoRelatorioSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Apenas admins podem ver/editar
        if not self.request.user.is_admin:
            return ConfiguracaoRelatorio.objects.none()
        return super().get_queryset()


class RelatorioGeradoViewSet(viewsets.ModelViewSet):
    """ViewSet para gerenciar relatórios gerados"""
    
    queryset = RelatorioGerado.objects.all()
    serializer_class = RelatorioGeradoSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin:
            return RelatorioGerado.objects.all()
        # Usuário normal vê apenas seus próprios relatórios
        return RelatorioGerado.objects.filter(usuario_gerador=user)
    
    def create(self, request, *args, **kwargs):
        """Criar novo relatório"""
        return Response(
            {"detail": "Use os endpoints específicos para gerar relatórios"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=False, methods=['post'])
    def gerar_resumo_geral(self, request):
        """Gera relatório de resumo geral"""
        data_inicio = request.data.get('data_inicio')
        data_fim = request.data.get('data_fim')
        formato = request.data.get('formato', 'json')
        
        try:
            if data_inicio:
                data_inicio = datetime.fromisoformat(data_inicio).date()
            if data_fim:
                data_fim = datetime.fromisoformat(data_fim).date()
        except ValueError:
            return Response(
                {"detail": "Formato de data inválido. Use YYYY-MM-DD"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        gerador = GeradorRelatorios(
            usuario=request.user,
            data_inicio=data_inicio,
            data_fim=data_fim
        )
        
        dados = gerador.gerar_resumo_geral()
        
        # Salvar relatório no banco
        relatorio = RelatorioGerado.objects.create(
            titulo="Resumo Geral de Métricas",
            tipo='resumo_geral',
            formato=formato,
            usuario_gerador=request.user,
            data_inicio=data_inicio,
            data_fim=data_fim,
            dados_json=dados
        )
        
        # Gerar arquivo se não for JSON
        if formato != 'json':
            arquivo_bytes = self._gerar_arquivo(dados, formato, relatorio.titulo)
            if arquivo_bytes:
                relatorio.arquivo.save(
                    f"resumo_geral_{timezone.now().strftime('%Y%m%d_%H%M%S')}.{formato}",
                    ContentFile(arquivo_bytes),
                    save=True
                )
        
        serializer = RelatorioGeradoSerializer(relatorio)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'])
    def gerar_performance_assessor(self, request):
        """Gera relatório de performance de assessores"""
        
        data_inicio = request.data.get('data_inicio')
        data_fim = request.data.get('data_fim')
        assessor_id = request.data.get('assessor_id')
        formato = request.data.get('formato', 'json')
        
        try:
            if data_inicio:
                data_inicio = datetime.fromisoformat(data_inicio).date()
            if data_fim:
                data_fim = datetime.fromisoformat(data_fim).date()
        except ValueError:
            return Response(
                {"detail": "Formato de data inválido. Use YYYY-MM-DD"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        gerador = GeradorRelatorios(
            usuario=request.user,
            data_inicio=data_inicio,
            data_fim=data_fim
        )
        
        dados = gerador.gerar_performance_assessor(assessor_id=assessor_id)
        
        assessor = None
        if assessor_id:
            assessor = get_object_or_404(CustomUser, id=assessor_id, is_assessor=True)
            titulo = f"Performance - {assessor.get_full_name()}"
        else:
            titulo = "Performance de Todos os Assessores"
        
        relatorio = RelatorioGerado.objects.create(
            titulo=titulo,
            tipo='performance_assessor',
            formato=formato,
            usuario_gerador=request.user,
            data_inicio=data_inicio,
            data_fim=data_fim,
            assessor=assessor,
            dados_json={'assessores': dados}
        )
        
        if formato != 'json':
            arquivo_bytes = self._gerar_arquivo(dados, formato, titulo)
            if arquivo_bytes:
                relatorio.arquivo.save(
                    f"performance_assessor_{timezone.now().strftime('%Y%m%d_%H%M%S')}.{formato}",
                    ContentFile(arquivo_bytes),
                    save=True
                )
        
        serializer = RelatorioGeradoSerializer(relatorio)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'])
    def gerar_status_empresas(self, request):
        """Gera relatório de status de empresas"""
        
        data_inicio = request.data.get('data_inicio')
        data_fim = request.data.get('data_fim')
        empresa_id = request.data.get('empresa_id')
        formato = request.data.get('formato', 'json')
        status_filter = request.data.get('status')
        
        try:
            if data_inicio:
                data_inicio = datetime.fromisoformat(data_inicio).date()
            if data_fim:
                data_fim = datetime.fromisoformat(data_fim).date()
        except ValueError:
            return Response(
                {"detail": "Formato de data inválido. Use YYYY-MM-DD"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        gerador = GeradorRelatorios(
            usuario=request.user,
            data_inicio=data_inicio,
            data_fim=data_fim
        )
        
        dados = gerador.gerar_status_empresas(empresa_id=empresa_id)
        
        if status_filter:
            dados = [e for e in dados if e['status'].lower() == status_filter.lower()]
        
        empresa = None
        if empresa_id:
            empresa = get_object_or_404(Empresa, id=empresa_id)
            titulo = f"Status - {empresa.nome}"
        else:
            titulo = "Status de Todas as Empresas"
        
        relatorio = RelatorioGerado.objects.create(
            titulo=titulo,
            tipo='status_empresas',
            formato=formato,
            usuario_gerador=request.user,
            data_inicio=data_inicio,
            data_fim=data_fim,
            empresa=empresa,
            dados_json={'empresas': dados}
        )
        
        if formato != 'json':
            arquivo_bytes = self._gerar_arquivo(dados, formato, titulo)
            if arquivo_bytes:
                relatorio.arquivo.save(
                    f"status_empresas_{timezone.now().strftime('%Y%m%d_%H%M%S')}.{formato}",
                    ContentFile(arquivo_bytes),
                    save=True
                )
        
        serializer = RelatorioGeradoSerializer(relatorio)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'])
    def gerar_visitas_detalhadas(self, request):
        """Gera relatório detalhado de visitas"""
        
        data_inicio = request.data.get('data_inicio')
        data_fim = request.data.get('data_fim')
        empresa_id = request.data.get('empresa_id')
        assessor_id = request.data.get('assessor_id')
        formato = request.data.get('formato', 'json')
        
        try:
            if data_inicio:
                data_inicio = datetime.fromisoformat(data_inicio).date()
            if data_fim:
                data_fim = datetime.fromisoformat(data_fim).date()
        except ValueError:
            return Response(
                {"detail": "Formato de data inválido. Use YYYY-MM-DD"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        gerador = GeradorRelatorios(
            usuario=request.user,
            data_inicio=data_inicio,
            data_fim=data_fim
        )
        
        dados = gerador.gerar_visitas_detalhadas(
            empresa_id=empresa_id,
            assessor_id=assessor_id
        )
        
        relatorio = RelatorioGerado.objects.create(
            titulo="Visitas Detalhadas",
            tipo='visitas_detalhadas',
            formato=formato,
            usuario_gerador=request.user,
            data_inicio=data_inicio,
            data_fim=data_fim,
            dados_json={'visitas': dados}
        )
        
        if formato != 'json':
            arquivo_bytes = self._gerar_arquivo(dados, formato, "Visitas Detalhadas")
            if arquivo_bytes:
                relatorio.arquivo.save(
                    f"visitas_detalhadas_{timezone.now().strftime('%Y%m%d_%H%M%S')}.{formato}",
                    ContentFile(arquivo_bytes),
                    save=True
                )
        
        serializer = RelatorioGeradoSerializer(relatorio)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'])
    def gerar_jornadas(self, request):
        """Gera relatório de jornadas e quilometragem"""
        
        data_inicio = request.data.get('data_inicio')
        data_fim = request.data.get('data_fim')
        assessor_id = request.data.get('assessor_id')
        formato = request.data.get('formato', 'json')
        
        try:
            if data_inicio:
                data_inicio = datetime.fromisoformat(data_inicio).date()
            if data_fim:
                data_fim = datetime.fromisoformat(data_fim).date()
        except ValueError:
            return Response(
                {"detail": "Formato de data inválido. Use YYYY-MM-DD"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        gerador = GeradorRelatorios(
            usuario=request.user,
            data_inicio=data_inicio,
            data_fim=data_fim
        )
        
        dados = gerador.gerar_jornadas_resumo(assessor_id=assessor_id)
        
        assessor = None
        if assessor_id:
            assessor = get_object_or_404(CustomUser, id=assessor_id, is_assessor=True)
            titulo = f"Jornadas - {assessor.get_full_name()}"
        else:
            titulo = "Jornadas e Quilometragem"
        
        relatorio = RelatorioGerado.objects.create(
            titulo=titulo,
            tipo='jornadas',
            formato=formato,
            usuario_gerador=request.user,
            data_inicio=data_inicio,
            data_fim=data_fim,
            assessor=assessor,
            dados_json={'jornadas': dados}
        )
        
        if formato != 'json':
            arquivo_bytes = self._gerar_arquivo(dados, formato, titulo)
            if arquivo_bytes:
                relatorio.arquivo.save(
                    f"jornadas_{timezone.now().strftime('%Y%m%d_%H%M%S')}.{formato}",
                    ContentFile(arquivo_bytes),
                    save=True
                )
        
        serializer = RelatorioGeradoSerializer(relatorio)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'])
    def gerar_conversoes(self, request):
        """Gera relatório de conversão de empresas"""
        
        data_inicio = request.data.get('data_inicio')
        data_fim = request.data.get('data_fim')
        formato = request.data.get('formato', 'json')
        
        try:
            if data_inicio:
                data_inicio = datetime.fromisoformat(data_inicio).date()
            if data_fim:
                data_fim = datetime.fromisoformat(data_fim).date()
        except ValueError:
            return Response(
                {"detail": "Formato de data inválido. Use YYYY-MM-DD"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        gerador = GeradorRelatorios(
            usuario=request.user,
            data_inicio=data_inicio,
            data_fim=data_fim
        )
        
        dados = gerador.gerar_conversoes()
        
        relatorio = RelatorioGerado.objects.create(
            titulo="Taxa de Conversão de Empresas",
            tipo='conversoes',
            formato=formato,
            usuario_gerador=request.user,
            data_inicio=data_inicio,
            data_fim=data_fim,
            dados_json={'conversoes': dados}
        )
        
        if formato != 'json':
            arquivo_bytes = self._gerar_arquivo(dados, formato, "Conversões")
            if arquivo_bytes:
                relatorio.arquivo.save(
                    f"conversoes_{timezone.now().strftime('%Y%m%d_%H%M%S')}.{formato}",
                    ContentFile(arquivo_bytes),
                    save=True
                )
        
        serializer = RelatorioGeradoSerializer(relatorio)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'])
    def gerar_feedback(self, request):
        """Gera relatório de feedback de visitas"""
        
        data_inicio = request.data.get('data_inicio')
        data_fim = request.data.get('data_fim')
        formato = request.data.get('formato', 'json')
        
        try:
            if data_inicio:
                data_inicio = datetime.fromisoformat(data_inicio).date()
            if data_fim:
                data_fim = datetime.fromisoformat(data_fim).date()
        except ValueError:
            return Response(
                {"detail": "Formato de data inválido. Use YYYY-MM-DD"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        gerador = GeradorRelatorios(
            usuario=request.user,
            data_inicio=data_inicio,
            data_fim=data_fim
        )
        
        dados = gerador.gerar_feedback_visitas()
        
        relatorio = RelatorioGerado.objects.create(
            titulo="Feedback das Visitas",
            tipo='feedback_visitas',
            formato=formato,
            usuario_gerador=request.user,
            data_inicio=data_inicio,
            data_fim=data_fim,
            dados_json={'feedback': dados}
        )
        
        if formato != 'json':
            arquivo_bytes = self._gerar_arquivo(dados, formato, "Feedback")
            if arquivo_bytes:
                relatorio.arquivo.save(
                    f"feedback_visitas_{timezone.now().strftime('%Y%m%d_%H%M%S')}.{formato}",
                    ContentFile(arquivo_bytes),
                    save=True
                )
        
        serializer = RelatorioGeradoSerializer(relatorio)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def listar_tipos(self, request):
        """Lista tipos de relatórios disponíveis"""
        tipos = [
            {
                'id': 'resumo_geral',
                'nome': 'Resumo Geral',
                'descricao': 'Métricas gerais de visitas, empresas e conversões'
            },
            {
                'id': 'performance_assessor',
                'nome': 'Performance do Assessor',
                'descricao': 'Dados de performance individual de assessores'
            },
            {
                'id': 'status_empresas',
                'nome': 'Status de Empresas',
                'descricao': 'Situação atual de todas as empresas'
            },
            {
                'id': 'visitas_detalhadas',
                'nome': 'Visitas Detalhadas',
                'descricao': 'Informações completas de cada visita realizada'
            },
            {
                'id': 'jornadas',
                'nome': 'Jornadas e Quilometragem',
                'descricao': 'Dados de jornadas de trabalho e quilometragem'
            },
            {
                'id': 'conversoes',
                'nome': 'Taxa de Conversão',
                'descricao': 'Análise de empresas convertidas de negociação para ativa'
            },
            {
                'id': 'feedback_visitas',
                'nome': 'Feedback das Visitas',
                'descricao': 'Respostas de formulários e feedback coletado'
            },
        ]
        return Response(tipos)
    
    @action(detail=False, methods=['get'])
    def listar_formatos(self, request):
        """Lista formatos de exportação disponíveis"""
        formatos = [
            {'id': 'json', 'nome': 'JSON', 'extensao': '.json'},
            {'id': 'csv', 'nome': 'CSV', 'extensao': '.csv'},
            {'id': 'excel', 'nome': 'Excel', 'extensao': '.xlsx'},
            {'id': 'pdf', 'nome': 'PDF', 'extensao': '.pdf'},
        ]
        return Response(formatos)
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Faz download do arquivo do relatório"""
        relatorio = self.get_object()
        
        if not relatorio.arquivo:
            return Response(
                {"detail": "Este relatório não tem arquivo para download"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return FileResponse(
            relatorio.arquivo.open('rb'),
            as_attachment=True,
            filename=f"{relatorio.titulo}_{timezone.now().strftime('%Y%m%d')}.{relatorio.formato}"
        )
    
    def _gerar_arquivo(self, dados, formato, titulo):
        """Helper para gerar arquivo em diferentes formatos"""
        try:
            if formato == 'csv':
                if isinstance(dados, list):
                    return ExportadorRelatorios.exportar_csv(dados, titulo).encode('utf-8')
            elif formato == 'excel':
                if isinstance(dados, list):
                    return ExportadorRelatorios.exportar_excel(dados, titulo)
            elif formato == 'pdf':
                return ExportadorRelatorios.exportar_pdf(dados, titulo)
        except Exception as e:
            print(f"Erro ao gerar arquivo {formato}: {e}")
        return None


class TemplatePessoalizadoViewSet(viewsets.ModelViewSet):
    """ViewSet para gerenciar templates personalizados de relatórios"""
    
    queryset = TemplatePessoalizado.objects.all()
    serializer_class = TemplatePessoalizadoSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        return TemplatePessoalizado.objects.filter(criador=user)
    
    def perform_create(self, serializer):
        serializer.save(criador=self.request.user)
