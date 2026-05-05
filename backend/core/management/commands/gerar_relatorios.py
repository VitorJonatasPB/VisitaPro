"""
Management command para gerar relatórios automaticamente.
Uso: python manage.py gerar_relatorios --tipo resumo_geral --formato pdf
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from core.relatorios_models import RelatorioGerado
from core.relatorios_utils import GeradorRelatorios, ExportadorRelatorios
from django.core.files.base import ContentFile

User = get_user_model()


class Command(BaseCommand):
    help = 'Gera relatórios automaticamente'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tipo',
            type=str,
            default='resumo_geral',
            help='Tipo de relatório (resumo_geral, performance_assessor, etc)'
        )
        parser.add_argument(
            '--formato',
            type=str,
            default='json',
            help='Formato de exportação (json, csv, excel, pdf)'
        )
        parser.add_argument(
            '--admin',
            type=int,
            default=1,
            help='ID do usuário admin para gerar o relatório'
        )
        parser.add_argument(
            '--dias',
            type=int,
            default=30,
            help='Número de dias para o período'
        )
        parser.add_argument(
            '--assessor',
            type=int,
            default=None,
            help='ID do assessor (para alguns tipos de relatório)'
        )
        parser.add_argument(
            '--empresa',
            type=int,
            default=None,
            help='ID da empresa (para alguns tipos de relatório)'
        )

    def handle(self, *args, **options):
        tipo = options['tipo']
        formato = options['formato']
        admin_id = options['admin']
        dias = options['dias']
        assessor_id = options.get('assessor')
        empresa_id = options.get('empresa')

        try:
            usuario = User.objects.get(id=admin_id, is_admin=True)
        except User.DoesNotExist:
            raise CommandError(f'Usuário admin com ID {admin_id} não encontrado')

        data_fim = timezone.now().date()
        data_inicio = data_fim - timedelta(days=dias)

        self.stdout.write(f'Gerando relatório: {tipo}')
        self.stdout.write(f'Período: {data_inicio} a {data_fim}')
        self.stdout.write(f'Formato: {formato}')

        gerador = GeradorRelatorios(
            usuario=usuario,
            data_inicio=data_inicio,
            data_fim=data_fim
        )

        try:
            # Gerar dados conforme tipo
            if tipo == 'resumo_geral':
                dados = gerador.gerar_resumo_geral()
                titulo = "Resumo Geral"
            
            elif tipo == 'performance_assessor':
                dados = gerador.gerar_performance_assessor(assessor_id)
                dados = {'assessores': dados}
                titulo = "Performance de Assessor"
            
            elif tipo == 'status_empresas':
                dados = gerador.gerar_status_empresas(empresa_id)
                dados = {'empresas': dados}
                titulo = "Status de Empresas"
            
            elif tipo == 'visitas_detalhadas':
                dados = gerador.gerar_visitas_detalhadas(empresa_id, assessor_id)
                dados = {'visitas': dados}
                titulo = "Visitas Detalhadas"
            
            elif tipo == 'jornadas':
                dados = gerador.gerar_jornadas_resumo(assessor_id)
                dados = {'jornadas': dados}
                titulo = "Jornadas"
            
            elif tipo == 'conversoes':
                dados = gerador.gerar_conversoes()
                dados = {'conversoes': dados}
                titulo = "Conversões"
            
            elif tipo == 'feedback_visitas':
                dados = gerador.gerar_feedback_visitas()
                dados = {'feedback': dados}
                titulo = "Feedback de Visitas"
            
            else:
                raise CommandError(f'Tipo de relatório inválido: {tipo}')

            # Criar registro de relatório
            relatorio = RelatorioGerado.objects.create(
                titulo=titulo,
                tipo=tipo,
                formato=formato,
                usuario_gerador=usuario,
                data_inicio=data_inicio,
                data_fim=data_fim,
                dados_json=dados
            )

            # Gerar arquivo se não for JSON
            if formato != 'json':
                dados_para_exportacao = dados.get(list(dados.keys())[0]) if isinstance(dados, dict) else dados
                
                if formato == 'csv':
                    arquivo_bytes = ExportadorRelatorios.exportar_csv(
                        dados_para_exportacao if isinstance(dados_para_exportacao, list) else [dados_para_exportacao],
                        titulo
                    ).encode('utf-8')
                    ext = 'csv'
                
                elif formato == 'excel':
                    arquivo_bytes = ExportadorRelatorios.exportar_excel(
                        dados_para_exportacao if isinstance(dados_para_exportacao, list) else [dados_para_exportacao],
                        titulo
                    )
                    ext = 'xlsx'
                
                elif formato == 'pdf':
                    arquivo_bytes = ExportadorRelatorios.exportar_pdf(dados, titulo)
                    ext = 'pdf'
                
                if arquivo_bytes:
                    relatorio.arquivo.save(
                        f"{titulo.replace(' ', '_')}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.{ext}",
                        ContentFile(arquivo_bytes),
                        save=True
                    )
                    self.stdout.write(self.style.SUCCESS(f'✓ Arquivo gerado: {relatorio.arquivo.name}'))

            self.stdout.write(self.style.SUCCESS(f'✓ Relatório #{relatorio.id} gerado com sucesso'))
            self.stdout.write(self.style.SUCCESS(f'✓ Tipo: {relatorio.get_tipo_display()}'))
            self.stdout.write(self.style.SUCCESS(f'✓ Formato: {relatorio.formato.upper()}'))

        except Exception as e:
            raise CommandError(f'Erro ao gerar relatório: {str(e)}')
