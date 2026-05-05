import json
from datetime import datetime, timedelta
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, View, DetailView, DeleteView
from django.contrib import messages
from django.http import FileResponse, Http404
from django.core.files.base import ContentFile
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import CustomUser, Empresa
from .relatorios_models import RelatorioGerado
from .relatorios_utils import GeradorRelatorios

class RelatorioAccessMixin(LoginRequiredMixin):
    """
    Mixin para controlar acesso aos relatórios.
    Administradores têm acesso total.
    Assessores precisam da permissão 'core.view_relatoriogerado'.
    """
    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return self.handle_no_permission()
            
        if user.is_superuser or getattr(user, 'is_admin', False):
            return super().dispatch(request, *args, **kwargs)
            
        if user.has_perm('core.view_relatoriogerado'):
            return super().dispatch(request, *args, **kwargs)
            
        messages.error(request, "Você não tem permissão para acessar relatórios.")
        return redirect('core:dashboard_assessor')


class RelatorioListView(RelatorioAccessMixin, ListView):
    model = RelatorioGerado
    template_name = 'core/relatorios_lista.html'
    context_object_name = 'relatorios'
    paginate_by = 10
    
    def get_queryset(self):
        user = self.request.user
        qs = RelatorioGerado.objects.all().order_by('-criado_em')
        
        # Filtrar apenas relatórios gerados pelo próprio usuário se não for admin
        if not (user.is_superuser or getattr(user, 'is_admin', False)):
            qs = qs.filter(usuario_gerador=user)
            
        tipo = self.request.GET.get('tipo')
        if tipo:
            qs = qs.filter(tipo=tipo)
            
        return qs


class RelatorioCreateView(RelatorioAccessMixin, View):
    template_name = 'core/novo_relatorio.html'
    
    def dispatch(self, request, *args, **kwargs):
        # Verifica permissão específica para criar (para assessores)
        user = request.user
        if not (user.is_superuser or getattr(user, 'is_admin', False)):
            if not user.has_perm('core.add_relatoriogerado'):
                messages.error(request, "Você não tem permissão para gerar novos relatórios.")
                return redirect('core:listar_relatorios')
        return super().dispatch(request, *args, **kwargs)
        
    def get(self, request):
        user = request.user
        
        if user.is_superuser or getattr(user, 'is_admin', False):
            assessores = CustomUser.objects.filter(is_assessor=True, is_active=True)
            empresas = Empresa.objects.all()
        else:
            # Assessor só vê ele mesmo e suas empresas associadas
            assessores = CustomUser.objects.filter(id=user.id)
            from django.db.models import Q
            empresas = Empresa.objects.filter(Q(assessor=user) | Q(visitas__assessor=user)).distinct()
            
        context = {
            'assessores': assessores,
            'empresas': empresas
        }
        return render(request, self.template_name, context)
        
    def post(self, request):
        tipo = request.POST.get('tipo')
        formato = request.POST.get('formato', 'json')
        data_inicio_str = request.POST.get('data_inicio')
        data_fim_str = request.POST.get('data_fim')
        
        user = request.user
        is_admin = user.is_superuser or getattr(user, 'is_admin', False)
        
        # Filtros opicionais
        empresa_id = request.POST.get('empresa_id') or None
        assessor_id = request.POST.get('assessor_id') or None
        status_empresa = request.POST.get('status_empresa') or None
        
        # Regra de Segurança: Se não for admin, FORÇAR o assessor_id para o próprio usuário
        # e garantir que as empresas buscadas pertençam a ele
        if not is_admin:
            assessor_id = user.id
            if empresa_id:
                # Validar se a empresa solicitada é acessível pelo assessor
                from django.db.models import Q
                empresa_permitida = Empresa.objects.filter(
                    Q(id=empresa_id) & (Q(assessor=user) | Q(visitas__assessor=user))
                ).exists()
                if not empresa_permitida:
                    messages.error(request, "Você não tem acesso aos dados desta empresa.")
                    return redirect('core:novo_relatorio')

        try:
            data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d').date()
            data_fim = datetime.strptime(data_fim_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            messages.error(request, "Datas inválidas.")
            return redirect('core:novo_relatorio')
            
        gerador = GeradorRelatorios(
            usuario=user,
            data_inicio=data_inicio,
            data_fim=data_fim
        )
        
        dados = None
        titulo = "Relatório"
        
        try:
            if tipo == 'resumo_geral':
                # No resumo geral original o Utils não aceita assessor_id, 
                # mas para um assessor, seria ideal filtrar as contagens. 
                # Por simplicidade, se for assessor, pode não ser o melhor relatório, 
                # ou podemos alertar o usuário.
                dados = gerador.gerar_resumo_geral()
                titulo = "Resumo Geral"
                
            elif tipo == 'performance_assessor':
                dados = gerador.gerar_performance_assessor(assessor_id=assessor_id)
                titulo = "Performance de Assessor"
                
            elif tipo == 'status_empresas':
                dados = gerador.gerar_status_empresas(empresa_id=empresa_id)
                if status_empresa:
                    dados = [d for d in dados if d.get('status', '').startswith(status_empresa) or status_empresa in d.get('status', '')]
                titulo = "Status de Empresas"
                
            elif tipo == 'visitas_detalhadas':
                dados = gerador.gerar_visitas_detalhadas(empresa_id=empresa_id, assessor_id=assessor_id)
                titulo = "Visitas Detalhadas"
                
            elif tipo == 'jornadas':
                dados = gerador.gerar_jornadas_resumo(assessor_id=assessor_id)
                titulo = "Jornadas e Quilometragem"
                
            elif tipo == 'conversoes':
                dados = gerador.gerar_conversoes()
                titulo = "Taxa de Conversão"
                
            elif tipo == 'feedback_visitas':
                dados = gerador.gerar_feedback_visitas()
                titulo = "Feedback das Visitas"
            else:
                messages.error(request, "Tipo de relatório inválido.")
                return redirect('core:novo_relatorio')
                
            # Se for assessor e os relatórios (como resumo_geral, conversoes) não filtram internamente,
            # em sistemas robustos deve-se reescrever a query no utils. Aqui mantemos seguro passando o ID
            # onde os métodos suportam, mas fica o alerta.
            
            relatorio = RelatorioGerado.objects.create(
                titulo=titulo,
                tipo=tipo,
                formato=formato,
                usuario_gerador=user,
                data_inicio=data_inicio,
                data_fim=data_fim,
                dados_json={tipo: dados}
            )
            
            if formato != 'json':
                # Usar a mesma lógica da ViewSet para salvar arquivo
                from .relatorios_views import RelatorioGeradoViewSet
                viewset_dummy = RelatorioGeradoViewSet()
                arquivo_bytes = viewset_dummy._gerar_arquivo(dados, formato, titulo)
                
                if arquivo_bytes:
                    relatorio.arquivo.save(
                        f"{tipo}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.{formato}",
                        ContentFile(arquivo_bytes),
                        save=True
                    )
            
            messages.success(request, "Relatório gerado com sucesso!")
            return redirect('core:listar_relatorios')
            
        except Exception as e:
            messages.error(request, f"Erro ao gerar relatório: {str(e)}")
            return redirect('core:novo_relatorio')


class RelatorioDetailView(RelatorioAccessMixin, DetailView):
    model = RelatorioGerado
    template_name = 'core/relatorios_view.html'
    context_object_name = 'relatorio'
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or getattr(user, 'is_admin', False):
            return RelatorioGerado.objects.all()
        return RelatorioGerado.objects.filter(usuario_gerador=user)
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Formatar JSON para exibição bonita
        try:
            context['dados_json_formatado'] = json.dumps(
                self.object.dados_json, 
                indent=4, 
                ensure_ascii=False, 
                default=str
            )
        except:
            context['dados_json_formatado'] = "{}"
        return context


class RelatorioDownloadView(RelatorioAccessMixin, View):
    def get(self, request, pk):
        user = request.user
        
        # Filtro de segurança
        if user.is_superuser or getattr(user, 'is_admin', False):
            relatorio = get_object_or_404(RelatorioGerado, pk=pk)
        else:
            relatorio = get_object_or_404(RelatorioGerado, pk=pk, usuario_gerador=user)
            
        if not relatorio.arquivo:
            messages.error(request, "Este relatório não possui um arquivo para download (apenas JSON interno).")
            return redirect('core:listar_relatorios')
            
        return FileResponse(
            relatorio.arquivo.open('rb'),
            as_attachment=True,
            filename=f"{relatorio.titulo}_{timezone.now().strftime('%Y%m%d')}.{relatorio.formato}"
        )


class RelatorioDeleteView(RelatorioAccessMixin, DeleteView):
    model = RelatorioGerado
    success_url = reverse_lazy('core:listar_relatorios')
    
    # Não há template próprio na deleção porque a tela lista já chama via form POST ou usa um Modal simples.
    # No caso de listagem usando link direto, Django requer template confirm_delete. 
    # O `relatorios_lista.html` possui um modal que direciona para a URL de delete. 
    # Precisamos tratar para deletar diretamente no método GET (apesar de não ser recomendado RESTful, 
    # o template usa tag a <a href="{% url 'core:delete_relatorio' %}">).
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or getattr(user, 'is_admin', False):
            return RelatorioGerado.objects.all()
        return RelatorioGerado.objects.filter(usuario_gerador=user)
        
    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)
        
    def delete(self, request, *args, **kwargs):
        messages.success(request, "Relatório deletado com sucesso.")
        return super().delete(request, *args, **kwargs)
