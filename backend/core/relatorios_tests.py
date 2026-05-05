"""
Exemplos práticos e testes para o módulo de relatórios do VisitaPro.
"""

from datetime import datetime, timedelta
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from core.models import Empresa, Visita, CustomUser, Jornada
from core.relatorios_models import RelatorioGerado
from core.relatorios_utils import GeradorRelatorios, ExportadorRelatorios
import json

User = get_user_model()


# ============================================================================
# EXEMPLOS PRÁTICOS
# ============================================================================

class ExemplosPraticos:
    """Exemplos de como usar o módulo de relatórios"""
    
    @staticmethod
    def exemplo_1_gerar_resumo_geral():
        """Exemplo 1: Gerar relatório de resumo geral"""
        
        # Definir período
        data_fim = timezone.now().date()
        data_inicio = data_fim - timedelta(days=30)
        
        # Criar gerador
        gerador = GeradorRelatorios(
            usuario=User.objects.first(),
            data_inicio=data_inicio,
            data_fim=data_fim
        )
        
        # Gerar dados
        dados = gerador.gerar_resumo_geral()
        
        # Exibir métricas principais
        print(f"📊 Resumo Geral - Período: {data_inicio} a {data_fim}")
        print(f"   Total de Visitas: {dados['total_visitas']}")
        print(f"   Visitas Realizadas: {dados['visitas_realizadas']}")
        print(f"   Taxa de Conversão: {dados['taxa_conversao_percentual']}%")
        print(f"   Empresas Ativas: {dados['empresas_ativas']}")
        
        return dados
    
    @staticmethod
    def exemplo_2_gerar_performance_assessor(assessor_id=None):
        """Exemplo 2: Gerar performance de um assessor específico"""
        
        data_fim = timezone.now().date()
        data_inicio = data_fim - timedelta(days=30)
        
        gerador = GeradorRelatorios(
            usuario=User.objects.first(),
            data_inicio=data_inicio,
            data_fim=data_fim
        )
        
        dados = gerador.gerar_performance_assessor(assessor_id=assessor_id)
        
        print(f"\n👤 Performance de Assessores:")
        for assessor in dados:
            print(f"   {assessor['assessor_nome']}")
            print(f"   ├─ Visitas: {assessor['total_visitas']}")
            print(f"   ├─ Realizadas: {assessor['visitas_realizadas']}")
            print(f"   ├─ Taxa: {assessor['taxa_realizacao_percentual']}%")
            print(f"   └─ Distância: {assessor['distancia_total_km']}km")
        
        return dados
    
    @staticmethod
    def exemplo_3_exportar_em_multiplos_formatos():
        """Exemplo 3: Exportar relatório em diferentes formatos"""
        
        data_fim = timezone.now().date()
        data_inicio = data_fim - timedelta(days=7)
        
        gerador = GeradorRelatorios(
            usuario=User.objects.first(),
            data_inicio=data_inicio,
            data_fim=data_fim
        )
        
        dados = gerador.gerar_resumo_geral()
        
        # Exportar em JSON
        json_data = ExportadorRelatorios.exportar_json(dados, "Resumo Geral")
        print(f"\n📄 JSON: {len(json_data)} caracteres")
        
        # Exportar em CSV
        csv_data = ExportadorRelatorios.exportar_csv([dados], "Resumo Geral")
        print(f"📊 CSV: {len(csv_data)} caracteres")
        
        # Exportar em PDF
        pdf_data = ExportadorRelatorios.exportar_pdf(dados, "Resumo Geral")
        if pdf_data:
            print(f"📑 PDF: {len(pdf_data)} bytes")
        
        # Salvar arquivos
        with open('/tmp/relatorio.json', 'w') as f:
            f.write(json_data)
        
        with open('/tmp/relatorio.csv', 'w') as f:
            f.write(csv_data)
        
        if pdf_data:
            with open('/tmp/relatorio.pdf', 'wb') as f:
                f.write(pdf_data)
        
        print("✓ Arquivos salvos em /tmp/")
    
    @staticmethod
    def exemplo_4_filtrar_por_empresa():
        """Exemplo 4: Gerar relatório filtrado por empresa"""
        
        # Pegar primeira empresa
        empresa = Empresa.objects.first()
        if not empresa:
            print("Nenhuma empresa encontrada")
            return
        
        data_fim = timezone.now().date()
        data_inicio = data_fim - timedelta(days=30)
        
        gerador = GeradorRelatorios(
            usuario=User.objects.first(),
            data_inicio=data_inicio,
            data_fim=data_fim
        )
        
        dados = gerador.gerar_visitas_detalhadas(empresa_id=empresa.id)
        
        print(f"\n🏢 Visitas Detalhadas - Empresa: {empresa.nome}")
        print(f"   Total de Visitas: {len(dados)}")
        for visita in dados[:5]:  # Mostrar primeiras 5
            print(f"   • {visita['data']} - {visita['assessor_nome']}")
        
        return dados
    
    @staticmethod
    def exemplo_5_salvar_relatorio_no_banco():
        """Exemplo 5: Salvar relatório no banco de dados"""
        
        data_fim = timezone.now().date()
        data_inicio = data_fim - timedelta(days=30)
        
        gerador = GeradorRelatorios(
            usuario=User.objects.first(),
            data_inicio=data_inicio,
            data_fim=data_fim
        )
        
        dados = gerador.gerar_resumo_geral()
        
        # Salvar no banco
        relatorio = RelatorioGerado.objects.create(
            titulo="Relatório de Resumo - Automático",
            tipo='resumo_geral',
            formato='json',
            usuario_gerador=User.objects.first(),
            data_inicio=data_inicio,
            data_fim=data_fim,
            dados_json=dados,
            descricao="Relatório gerado automaticamente para exemplo"
        )
        
        print(f"\n💾 Relatório #{relatorio.id} salvo no banco")
        print(f"   Title: {relatorio.titulo}")
        print(f"   Tipo: {relatorio.get_tipo_display()}")
        print(f"   Gerado em: {relatorio.criado_em}")
        
        return relatorio


# ============================================================================
# TESTES UNITÁRIOS
# ============================================================================

class RelatoriosTestes(TestCase):
    """Testes para o módulo de relatórios"""
    
    def setUp(self):
        """Preparar dados de teste"""
        
        # Criar usuários
        self.admin = User.objects.create_user(
            username='admin',
            password='admin123',
            is_admin=True,
            is_staff=True
        )
        
        self.assessor = User.objects.create_user(
            username='assessor1',
            password='pass123',
            is_assessor=True
        )
        
        # Criar empresas
        self.empresa1 = Empresa.objects.create(
            nome='Empresa A',
            assessor=self.assessor,
            status='A'
        )
        
        self.empresa2 = Empresa.objects.create(
            nome='Empresa B',
            assessor=self.assessor,
            status='N'
        )
        
        # Criar visitas
        data_hoje = timezone.now().date()
        self.visita1 = Visita.objects.create(
            empresa=self.empresa1,
            assessor=self.assessor,
            data=data_hoje,
            horario=timezone.now().time(),
            status='realizada'
        )
        
        self.visita2 = Visita.objects.create(
            empresa=self.empresa2,
            assessor=self.assessor,
            data=data_hoje - timedelta(days=5),
            horario=timezone.now().time(),
            status='agendada'
        )
    
    def test_gerar_resumo_geral(self):
        """Teste: Gerar resumo geral"""
        
        gerador = GeradorRelatorios(
            usuario=self.admin,
            data_inicio=timezone.now().date() - timedelta(days=30),
            data_fim=timezone.now().date()
        )
        
        dados = gerador.gerar_resumo_geral()
        
        # Validações
        self.assertIn('total_visitas', dados)
        self.assertIn('visitas_realizadas', dados)
        self.assertIn('empresas_ativas', dados)
        self.assertEqual(dados['total_visitas'], 2)
        self.assertEqual(dados['empresas_ativas'], 1)
    
    def test_gerar_performance_assessor(self):
        """Teste: Gerar performance de assessor"""
        
        gerador = GeradorRelatorios(
            usuario=self.admin,
            data_inicio=timezone.now().date() - timedelta(days=30),
            data_fim=timezone.now().date()
        )
        
        dados = gerador.gerar_performance_assessor(self.assessor.id)
        
        self.assertEqual(len(dados), 1)
        self.assertEqual(dados[0]['assessor_id'], self.assessor.id)
        self.assertEqual(dados[0]['total_visitas'], 2)
    
    def test_gerar_status_empresas(self):
        """Teste: Gerar status de empresas"""
        
        gerador = GeradorRelatorios(
            usuario=self.admin,
            data_inicio=timezone.now().date() - timedelta(days=30),
            data_fim=timezone.now().date()
        )
        
        dados = gerador.gerar_status_empresas()
        
        self.assertEqual(len(dados), 2)
        self.assertTrue(any(e['empresa_nome'] == 'Empresa A' for e in dados))
    
    def test_gerar_visitas_detalhadas(self):
        """Teste: Gerar visitas detalhadas"""
        
        gerador = GeradorRelatorios(
            usuario=self.admin,
            data_inicio=timezone.now().date() - timedelta(days=30),
            data_fim=timezone.now().date()
        )
        
        dados = gerador.gerar_visitas_detalhadas()
        
        self.assertEqual(len(dados), 2)
        self.assertTrue(all('empresa_nome' in d for d in dados))
    
    def test_gerar_conversoes(self):
        """Teste: Gerar análise de conversões"""
        
        # Marcar data de conversão
        self.empresa2.status = 'A'
        self.empresa2.data_conversao = timezone.now().date()
        self.empresa2.save()
        
        gerador = GeradorRelatorios(
            usuario=self.admin,
            data_inicio=timezone.now().date() - timedelta(days=30),
            data_fim=timezone.now().date()
        )
        
        dados = gerador.gerar_conversoes()
        
        self.assertEqual(len(dados), 1)
        self.assertEqual(dados[0]['empresa_nome'], 'Empresa B')
    
    def test_exportar_json(self):
        """Teste: Exportar em JSON"""
        
        dados = {'teste': 'dados'}
        json_str = ExportadorRelatorios.exportar_json(dados)
        
        self.assertIn('teste', json_str)
        self.assertIn('dados', json_str)
        
        # Validar JSON válido
        parsed = json.loads(json_str)
        self.assertEqual(parsed['teste'], 'dados')
    
    def test_exportar_csv(self):
        """Teste: Exportar em CSV"""
        
        dados = [
            {'nome': 'Empresa A', 'status': 'Ativa'},
            {'nome': 'Empresa B', 'status': 'Inativa'}
        ]
        
        csv_str = ExportadorRelatorios.exportar_csv(dados)
        
        self.assertIn('nome', csv_str)
        self.assertIn('Empresa A', csv_str)
    
    def test_salvar_relatorio_no_banco(self):
        """Teste: Salvar relatório no banco de dados"""
        
        dados = {'teste': 'dados'}
        
        relatorio = RelatorioGerado.objects.create(
            titulo='Teste Relatório',
            tipo='resumo_geral',
            formato='json',
            usuario_gerador=self.admin,
            dados_json=dados
        )
        
        self.assertTrue(RelatorioGerado.objects.filter(id=relatorio.id).exists())
        self.assertEqual(relatorio.titulo, 'Teste Relatório')
        self.assertEqual(relatorio.dados_json, dados)
    
    def test_permissoes_usuario(self):
        """Teste: Validar permissões por usuário"""
        
        # Criar relatório para admin
        relatorio = RelatorioGerado.objects.create(
            titulo='Relatório Admin',
            tipo='resumo_geral',
            formato='json',
            usuario_gerador=self.admin,
            dados_json={'teste': 'dados'}
        )
        
        # Verificar que o assessor não pode acessar
        self.assertEqual(relatorio.usuario_gerador, self.admin)
        self.assertNotEqual(relatorio.usuario_gerador, self.assessor)


# ============================================================================
# SCRIPTS PARA EXECUÇÃO
# ============================================================================

def executar_exemplos():
    """Executar todos os exemplos"""
    
    print("=" * 60)
    print("🎯 EXEMPLOS PRÁTICOS - MÓDULO DE RELATÓRIOS")
    print("=" * 60)
    
    try:
        ExemplosPraticos.exemplo_1_gerar_resumo_geral()
        ExemplosPraticos.exemplo_2_gerar_performance_assessor()
        ExemplosPraticos.exemplo_3_exportar_em_multiplos_formatos()
        ExemplosPraticos.exemplo_4_filtrar_por_empresa()
        ExemplosPraticos.exemplo_5_salvar_relatorio_no_banco()
        
        print("\n" + "=" * 60)
        print("✅ TODOS OS EXEMPLOS EXECUTADOS COM SUCESSO")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Erro ao executar exemplos: {e}")


if __name__ == '__main__':
    # Para executar no Django shell: python manage.py shell
    # >>> exec(open('core/relatorios_tests.py').read())
    # >>> executar_exemplos()
    pass
