from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse_lazy
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DeleteView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import JsonResponse, HttpResponse
from django.db import IntegrityError
import json
from django.conf import settings
from .models import Empresa, Visita, CustomUser, Funcionario, PerguntaRelatorio, RespostaRelatorio, Configuracao
from .forms import AssessorForm, AdminUserForm, EmpresaForm, VisitaForm, RelatorioVisitaForm, FuncionarioForm, PerguntaRelatorioForm, GroupForm, ConfiguracaoForm
from django.contrib.auth.models import Group
import pandas as pd
from django.contrib import messages
import csv
import io

class CustomLoginView(LoginView):
    template_name = 'core/login.html'
    redirect_authenticated_user = True
    
    def form_valid(self, form):
        response = super().form_valid(form)
        remember_me = self.request.POST.get('remember_me')
        if not remember_me:
            self.request.session.set_expiry(0)
        else:
            self.request.session.set_expiry(1209600) # 2 weeks
        return response
    
    def get_success_url(self):
        user = self.request.user
        if getattr(user, 'is_admin', False) or user.is_superuser:
            return reverse_lazy('core:dashboard_admin')
        elif getattr(user, 'is_assessor', False):
            return reverse_lazy('core:dashboard_assessor')
        # Fallback para admin se for superuser sem os campos booleanos marcados
        if user.is_superuser:
            return reverse_lazy('core:dashboard_admin')
        return reverse_lazy('core:dashboard_assessor')

def custom_logout(request):
    logout(request)
    return redirect('core:login')

class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser or self.request.user.is_admin
        
class AssessorRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_assessor

class DashboardAdminView(AdminRequiredMixin, TemplateView):
    template_name = 'core/dashboard_admin.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from django.utils import timezone
        import datetime
        import calendar
        hoje = timezone.now().date()
        mes_atual = hoje.month
        ano_atual = hoje.year

        # Filtro de Assessor
        assessor_id = self.request.GET.get('assessor_id')
        
        # Lista para o Select
        context['assessores_lista'] = CustomUser.objects.filter(is_assessor=True, is_active=True).order_by('first_name', 'username')
        context['assessor_id_selecionado'] = assessor_id
        
        # Assessor Atual e Iniciais
        iniciais = "TD"
        user_foto_url = None
        if assessor_id:
            try:
                assessor_obj = CustomUser.objects.get(id=int(assessor_id))
                if assessor_obj.first_name:
                    iniciais = assessor_obj.first_name[0].upper()
                    if assessor_obj.last_name:
                        iniciais += assessor_obj.last_name[0].upper()
                else:
                    iniciais = assessor_obj.username[:2].upper()
                user_foto_url = assessor_obj.foto.url if assessor_obj.foto else None
            except CustomUser.DoesNotExist:
                assessor_id = None
                user_foto_url = None
        
        context['user_initials'] = iniciais
        context['user_foto_url'] = user_foto_url
        
        # Filtrar as mÃ©tricas gerais baseado ou nÃ£o em assessor
        visitas_do_mes = Visita.objects.filter(data__year=ano_atual, data__month=mes_atual)
        if assessor_id:
            visitas_do_mes = visitas_do_mes.filter(assessor_id=assessor_id)
            
        context['agendadas_mes'] = visitas_do_mes.filter(status='agendada').count()
        context['visitas_realizadas_mes'] = visitas_do_mes.filter(status='realizada').count()
        context['canceladas_mes'] = visitas_do_mes.filter(status='cancelada').count()
        context['assessores_ativos'] = CustomUser.objects.filter(is_assessor=True, is_active=True).count()
        
        from django.db.models import Q
        empresas_qs = Empresa.objects.all()
        if assessor_id:
            empresas_qs = empresas_qs.filter(Q(assessor_id=assessor_id) | Q(visitas__assessor_id=assessor_id)).distinct()
        context['total_empresas'] = empresas_qs.count()
        
        from .models import Funcionario
        funcionarios_qs = Funcionario.objects.all()
        if assessor_id:
            funcionarios_qs = funcionarios_qs.filter(empresa__in=empresas_qs).distinct()
        context['total_funcionarios'] = funcionarios_qs.count()
        
        # Ãšltimas visitas
        ultimas_visitas = Visita.objects.all().order_by('-data', '-horario')
        if assessor_id:
            ultimas_visitas = ultimas_visitas.filter(assessor_id=assessor_id)
        context['ultimas_visitas'] = ultimas_visitas[:5]
        context['empresas_recentes'] = empresas_qs.order_by('-id')[:5]

        # Empresas no Mapa (se tiver filtro, mostra sÃ³ as dele)
        from django.db.models import Q
        empresas = Empresa.objects.all()
        if assessor_id:
            empresas = empresas.filter(Q(assessor_id=assessor_id) | Q(visitas__assessor_id=assessor_id)).distinct()
            
        empresas_mapa = []
        for e in empresas:
            cor = e.assessor.cor_mapa if e.assessor and hasattr(e.assessor, 'cor_mapa') else '#3B82F6'
            nome_assessor = e.assessor.get_full_name() or e.assessor.username if e.assessor else 'Sem assessor'
            empresas_mapa.append({
                'nome': e.nome,
                'lat': e.latitude,
                'lng': e.longitude,
                'cep': e.cep or '',
                'rua': e.rua or '',
                'numero': e.numero or '',
                'bairro': e.bairro or '',
                'cidade': e.cidade or '',
                'estado': e.estado or '',
                'status': e.get_status_display(),
                'url': str(reverse_lazy('core:empresa_update', kwargs={'pk': e.id})),
                'cor': cor,
                'assessor': nome_assessor,
            })
        context['empresas_mapa'] = json.dumps(empresas_mapa)
        
        # MÃ©trica p/ GrÃ¡fico de Colunas: FuncionÃ¡rios Atendidos nos Ãºltimos 6 meses
        grafico_labels = []
        grafico_data = []
        grafico_conversoes_data = []
        grafico_conversoes_data = []
        
        for i in range(4, -1, -1):
            mes = hoje.month - i
            ano = hoje.year
            if mes <= 0:
                mes += 12
                ano -= 1
                
            visitas_mes_ano = Visita.objects.filter(data__year=ano, data__month=mes, status='realizada')
            if assessor_id:
                visitas_mes_ano = visitas_mes_ano.filter(assessor_id=assessor_id)
                
            empresas_ids = set([v.empresa.id for v in visitas_mes_ano])
            total_empresas_visitadas = len(empresas_ids)
            
            nome_mes = calendar.month_abbr[mes]
            meses_ptbr = {1:'Jan', 2:'Fev', 3:'Mar', 4:'Abr', 5:'Mai', 6:'Jun', 7:'Jul', 8:'Ago', 9:'Set', 10:'Out', 11:'Nov', 12:'Dez'}
            nome_mes_br = meses_ptbr.get(mes, '')
            
            grafico_labels.append(f"{nome_mes_br}/{str(ano)[-2:]}")
            grafico_data.append(total_empresas_visitadas)
            
            empresas_base_qs = Empresa.objects.all()
            if assessor_id:
                empresas_base_qs = empresas_base_qs.filter(assessor_id=assessor_id)
            conversoes_mes_ano = empresas_base_qs.filter(data_conversao__year=ano, data_conversao__month=mes).count()
            grafico_conversoes_data.append(conversoes_mes_ano)
            
        context['grafico_labels'] = json.dumps(grafico_labels)
        context['grafico_data'] = json.dumps(grafico_data)
        context['grafico_conversoes_data'] = json.dumps(grafico_conversoes_data)
        
        # GrÃ¡fico de Rosca: Status das Empresas
        empresas_qs = Empresa.objects.all()
        if assessor_id:
            empresas_qs = empresas_qs.filter(assessor_id=assessor_id)
            
        ativas = empresas_qs.filter(status='A').count()
        inativas = empresas_qs.filter(status='I').count()
        negociacao = empresas_qs.filter(status='N').count()
        
        context['rosca_ativas'] = ativas
        context['rosca_inativas'] = inativas
        context['rosca_negociacao'] = negociacao
        
        # ConversÃ£o de Clientes (mÃªs atual)
        conversoes_mes = empresas_qs.filter(
            data_conversao__year=hoje.year,
            data_conversao__month=hoje.month
        ).count()
        context['conversoes_mes'] = conversoes_mes
        
        return context

class ManifestView(TemplateView):
    template_name = 'core/manifest.json'
    content_type = 'application/json'

class ServiceWorkerView(TemplateView):
    template_name = 'core/serviceworker.js'
    content_type = 'application/javascript'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empresas = Empresa.objects.exclude(latitude__isnull=True).exclude(latitude__exact='').exclude(longitude__isnull=True).exclude(longitude__exact='')
        empresas_mapa = []
        for e in empresas:
            empresas_mapa.append({
                'nome': e.nome,
                'lat': e.latitude,
                'lng': e.longitude,
                'url': str(reverse_lazy('core:empresa_update', kwargs={'pk': e.id}))
            })
        context['empresas_mapa'] = json.dumps(empresas_mapa)
        return context


class RotaPlanejadorView(LoginRequiredMixin, TemplateView):
    template_name = 'core/rota_planejador.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from .models import Empresa
        import json
        
        empresas = Empresa.objects.all()
        empresas_data = []
        for e in empresas:
            # Montar endereço completo para exibição e busca
            endereco = f"{e.rua or ''}, {e.numero or ''}, {e.cidade or ''} - {e.estado or ''}".strip(", ")
            empresas_data.append({
                'nome': e.nome,
                'endereco': endereco,
                'lat': float(e.latitude) if e.latitude else None,
                'lng': float(e.longitude) if e.longitude else None
            })
        
        from .models import Configuracao
        config = Configuracao.get_solo()
        context['valor_km_reembolso'] = float(config.valor_km_reembolso)
        
        context['empresas_json'] = json.dumps(empresas_data)
        return context

class SalvarJornadaDiaView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            km_total = float(data.get('km_total', 0))
            
            from django.utils import timezone
            import datetime
            
            data_str = data.get('data_jornada')
            if data_str:
                try:
                    data_alvo = datetime.datetime.strptime(data_str, '%Y-%m-%d').date()
                except ValueError:
                    data_alvo = timezone.now().date()
            else:
                data_alvo = timezone.now().date()
                
            from .models import Jornada
            
            # Verifica se já existe jornada nessa data para o usuário
            jornada, created = Jornada.objects.get_or_create(
                assessor=request.user,
                data=data_alvo,
                defaults={'km_total': km_total, 'status': 'finalizada'}
            )
            
            if not created:
                jornada.km_total = km_total
                jornada.status = 'finalizada'
                jornada.save()
                
            return JsonResponse({'status': 'success', 'message': 'Jornada do dia salva com sucesso!'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

class ConfiguracaoUpdateView(AdminRequiredMixin, UpdateView):
    model = Configuracao
    form_class = ConfiguracaoForm
    template_name = 'core/configuracoes.html'
    success_url = reverse_lazy('core:dashboard_admin')

    def get_object(self, queryset=None):
        return Configuracao.get_solo()

    def form_valid(self, form):
        messages.success(self.request, "Configurações atualizadas com sucesso!")
        return super().form_valid(form)

class DashboardAssessorView(AssessorRequiredMixin, TemplateView):
    template_name = 'core/dashboard_assessor.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        from django.db.models import Q
        empresas = Empresa.objects.filter(Q(assessor=user) | Q(visitas__assessor=user)).distinct()
        empresas_mapa = []
        for e in empresas:
            empresas_mapa.append({
                'nome': e.nome,
                'lat': e.latitude or '',
                'lng': e.longitude or '',
                'cep': e.cep or '',
                'rua': e.rua or '',
                'numero': e.numero or '',
                'bairro': e.bairro or '',
                'cidade': e.cidade or '',
                'estado': e.estado or '',
                'status': e.get_status_display(),
                'url': str(reverse_lazy('core:empresa_update', kwargs={'pk': e.id}))
            })
        context['empresas_mapa'] = json.dumps(empresas_mapa)
        context['empresas_recentes'] = empresas.order_by('-id')[:5]

        
        # Avatar (Iniciais)
        iniciais = ""
        if user.first_name:
            iniciais += user.first_name[0].upper()
        if user.last_name:
            iniciais += user.last_name[0].upper()
        
        if not iniciais and user.username:
            iniciais = user.username[0].upper()
            
        context['user_initials'] = iniciais
        context['user_foto_url'] = user.foto.url if user.foto else None
        
        # Filtros de Visitas do MÃªs para Assessor
        from django.utils import timezone
        import datetime
        import calendar
        
        hoje = timezone.now().date()
        mes_atual = hoje.month
        ano_atual = hoje.year
        
        visitas_do_assessor_mes = Visita.objects.filter(
            assessor=user, 
            data__year=ano_atual, 
            data__month=mes_atual
        )
        
        context['visitas_agendadas_mes'] = visitas_do_assessor_mes.filter(status='agendada').count()
        context['visitas_realizadas_mes'] = visitas_do_assessor_mes.filter(status='realizada').count()
        context['visitas_canceladas_mes'] = visitas_do_assessor_mes.filter(status='cancelada').count()
        
        # Manteve para caso seja usado em outro lugar no front
        context['proximas_visitas_mes'] = visitas_do_assessor_mes.filter(
            data__gte=hoje
        ).exclude(status='cancelada').count()
        
        context['visitas_hoje'] = Visita.objects.filter(
            assessor=user,
            data=hoje
        ).order_by('horario')
        
        context['total_empresas'] = empresas.count()
        from .models import Funcionario
        context['total_funcionarios'] = Funcionario.objects.filter(empresa__in=empresas).distinct().count()
        
        # MÃ©trica p/ GrÃ¡fico de Pizza: Contatoes Atendidos nos Ãºltimos 6 meses
        grafico_labels = []
        grafico_data = []
        
        # ComeÃ§amos do mÃªs atual caindo atÃ© 4 meses atrÃ¡s (Total 5)
        for i in range(4, -1, -1):
            mes = hoje.month - i
            ano = hoje.year
            if mes <= 0:
                mes += 12
                ano -= 1
                
            # Buscar visitas 'realizadas' naquele mes/ano para o assessor
            visitas_mes_ano = Visita.objects.filter(assessor=user, data__year=ano, data__month=mes, status='realizada')
            
            # Pegar o ID de todas as empresas dessas visitas
            empresas_ids = set([v.empresa.id for v in visitas_mes_ano])
            total_empresas_visitadas = len(empresas_ids)
            
            # Formatando o Nome do mes
            nome_mes = calendar.month_abbr[mes]  # ex: 'Jan', 'Feb' (Nota: por padrÃ£o pt-BR de locale, nÃ£o tem no Django sem Babel, usaremos um mapa fixo p/ BR se preferÃ­vel mas calendar Ã© ok)
            meses_ptbr = {1:'Jan', 2:'Fev', 3:'Mar', 4:'Abr', 5:'Mai', 6:'Jun', 7:'Jul', 8:'Ago', 9:'Set', 10:'Out', 11:'Nov', 12:'Dez'}
            nome_mes_br = meses_ptbr.get(mes, '')
            
            grafico_labels.append(f"{nome_mes_br}/{str(ano)[-2:]}")
            grafico_data.append(total_empresas_visitadas)
            
            empresas_base_qs = Empresa.objects.all()
            if assessor_id:
                empresas_base_qs = empresas_base_qs.filter(assessor_id=assessor_id)
            conversoes_mes_ano = empresas_base_qs.filter(data_conversao__year=ano, data_conversao__month=mes).count()
            grafico_conversoes_data.append(conversoes_mes_ano)
            
        context['grafico_labels'] = json.dumps(grafico_labels)
        context['grafico_data'] = json.dumps(grafico_data)
        context['grafico_conversoes_data'] = json.dumps(grafico_conversoes_data)
        
        # GrÃ¡fico de Rosca: Status das Empresas (Para o Assessor)
        empresas_qs = empresas
        
        ativas = empresas_qs.filter(status='A').count()
        inativas = empresas_qs.filter(status='I').count()
        negociacao = empresas_qs.filter(status='N').count()
        
        context['rosca_ativas'] = ativas
        context['rosca_inativas'] = inativas
        context['rosca_negociacao'] = negociacao
        
        # ConversÃ£o de Clientes (mÃªs atual)
        conversoes_mes = empresas_qs.filter(
            data_conversao__year=hoje.year,
            data_conversao__month=hoje.month
        ).count()
        context['conversoes_mes'] = conversoes_mes
        
        return context

# -- CRUD CONSULTOR (USER) --
class AssessorListView(AdminRequiredMixin, ListView):
    model = CustomUser
    template_name = 'core/assessor_list.html'
    context_object_name = 'assessores'
    
    def get_queryset(self):
        qs = CustomUser.objects.filter(is_assessor=True)
        nome = self.request.GET.get('nome')
        if nome:
            qs = qs.filter(first_name__icontains=nome) | qs.filter(username__icontains=nome)
        return qs

class AssessorCreateView(AdminRequiredMixin, CreateView):
    model = CustomUser
    form_class = AssessorForm
    template_name = 'core/assessor_form.html'
    success_url = reverse_lazy('core:assessor_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        from django.db import transaction, IntegrityError
        try:
            with transaction.atomic():
                return super().form_valid(form)
        except IntegrityError:
            form.add_error('username', 'Já existe um usuário com esse nome de usuário.')
            return self.form_invalid(form)

class AssessorUpdateView(AdminRequiredMixin, UpdateView):
    model = CustomUser
    form_class = AssessorForm
    template_name = 'core/assessor_form.html'
    success_url = reverse_lazy('core:assessor_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        from django.db import transaction, IntegrityError
        try:
            with transaction.atomic():
                return super().form_valid(form)
        except IntegrityError:
            form.add_error('username', 'Já existe um usuário com esse nome de usuário.')
            return self.form_invalid(form)

class AssessorDeleteView(AdminRequiredMixin, DeleteView):
    model = CustomUser
    template_name = 'core/assessor_confirm_delete.html'
    success_url = reverse_lazy('core:assessor_list')

# -- CRUD EMPRESA --
class EmpresaListView(LoginRequiredMixin, ListView):
    model = Empresa
    template_name = 'core/empresa_list.html'
    context_object_name = 'empresas'

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        
        # Filtros GET
        nome = self.request.GET.get('nome')
        status = self.request.GET.get('status')
        assessor_id = self.request.GET.get('assessor')

        estado = self.request.GET.get('estado')
        cidade = self.request.GET.get('cidade')

        if nome:
            qs = qs.filter(nome__icontains=nome)
        if status:
            qs = qs.filter(status=status)
        if assessor_id:
            qs = qs.filter(assessor_id=assessor_id)
        if estado:
            qs = qs.filter(estado__iexact=estado)
        if cidade:
            qs = qs.filter(cidade__icontains=cidade)

        if not (user.is_superuser or getattr(user, 'is_admin', False)):
            # Retorna apenas as empresas que esse assessor estÃ¡ designado como titular ou autorizado
            from django.db.models import Q
            qs = qs.filter(Q(assessor=user) | Q(assessores_autorizados=user)).distinct()
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        if user.is_superuser or getattr(user, 'is_admin', False):
            context['assessores_list'] = CustomUser.objects.filter(is_assessor=True)
        return context

class EmpresaCreateView(AdminRequiredMixin, CreateView):
    model = Empresa
    form_class = EmpresaForm
    template_name = 'core/empresa_form.html'
    success_url = reverse_lazy('core:empresa_list')

class EmpresaUpdateView(LoginRequiredMixin, UpdateView):
    model = Empresa
    form_class = EmpresaForm
    template_name = 'core/empresa_form.html'
    success_url = reverse_lazy('core:empresa_list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        user = self.request.user
        if not (user.is_superuser or getattr(user, 'is_admin', False)):
            for field in form.fields.values():
                field.disabled = True
        return form

    def post(self, request, *args, **kwargs):
        user = request.user
        if not (user.is_superuser or getattr(user, 'is_admin', False)):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("Apenas administradores podem editar.")
        return super().post(request, *args, **kwargs)

class EmpresaDeleteView(AdminRequiredMixin, DeleteView):
    model = Empresa
    template_name = 'core/empresa_confirm_delete.html'
    success_url = reverse_lazy('core:empresa_list')

# -- AGENDA / VISITAS --
class AgendaView(LoginRequiredMixin, TemplateView):
    template_name = 'core/agenda.html'

class VisitaListView(LoginRequiredMixin, ListView):
    model = Visita
    template_name = 'core/visita_list.html'
    context_object_name = 'visitas'

    def get_queryset(self):
        user = self.request.user
        from django.utils import timezone
        import datetime
        
        status_filter = self.request.GET.get('status')
        data_str = self.request.GET.get('data')
        
        # Se for passado um status, filtremos para as de todo o mÃªs atual
        if status_filter:
            hoje = timezone.now().date()
            self.data_alvo = None # Marca como nulo para usarmos no Context
            self.status_filtro_ativo = True
            
            qs = Visita.objects.filter(data__year=hoje.year, data__month=hoje.month, status=status_filter)
        else:
            self.status_filtro_ativo = False
            if data_str:
                try:
                    data_alvo = datetime.datetime.strptime(data_str, '%Y-%m-%d').date()
                except ValueError:
                    data_alvo = timezone.now().date()
            else:
                data_alvo = timezone.now().date()
                
            self.data_alvo = data_alvo
            qs = Visita.objects.filter(data=data_alvo).order_by('horario')

        if not (user.is_superuser or getattr(user, 'is_admin', False)):
            qs = qs.filter(assessor=user)
            
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        import datetime
        from django.utils import timezone
        
        user = self.request.user
        
        data_alvo = getattr(self, 'data_alvo', None)
        if hasattr(self, 'status_filtro_ativo') and self.status_filtro_ativo:
            # Sendo status ativo, a exibiÃ§Ã£o serÃ¡ mensal. Passaremos hoje apenas como base de calendÃ¡rio
            data_alvo = timezone.now().date()
            context['is_monthly_status'] = True
        else:
            context['is_monthly_status'] = False
            
        context['hoje'] = data_alvo
        context['dia_anterior'] = data_alvo - datetime.timedelta(days=1)
        context['proximo_dia'] = data_alvo + datetime.timedelta(days=1)
        
        # Obter a lista de dias que contÃ©m visitas atreladas a este usuÃ¡rio (Para o Flatpickr)
        if user.is_superuser or getattr(user, 'is_admin', False):
            visitas = Visita.objects.all()
        else:
            visitas = Visita.objects.filter(assessor=user)
        
        dias_com_visita = list(set([v.data.strftime('%Y-%m-%d') for v in visitas if v.data]))
        import json
        context['dias_com_visita'] = json.dumps(dias_com_visita)
        
        return context

class AgendaView(LoginRequiredMixin, TemplateView):
    template_name = 'core/agenda.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        from django.utils import timezone
        import datetime
        
        data_str = self.request.GET.get('data')
        try:
            if data_str:
                hoje = datetime.datetime.strptime(data_str, '%Y-%m-%d').date()
            else:
                hoje = timezone.now().date()
        except ValueError:
            hoje = timezone.now().date()
            
        context['data_selecionada'] = hoje
        context['is_hoje'] = (hoje == timezone.now().date())
        
        assessor_id = self.request.GET.get('assessor')
        
        if user.is_superuser or getattr(user, 'is_admin', False):
            context['assessores_list'] = CustomUser.objects.filter(is_assessor=True)
            visitas = Visita.objects.all().order_by('data', 'horario')
            if assessor_id:
                visitas = visitas.filter(assessor_id=assessor_id)
                context['assessor_id_selecionado'] = int(assessor_id)
        else:
            visitas = Visita.objects.filter(assessor=user).order_by('data', 'horario')
            
        periodo = self.request.GET.get('periodo', 'mes') # Por padrÃ£o foca no mÃªs atual
        context['periodo'] = periodo
        
        if periodo == 'dia':
            visitas = visitas.filter(data=hoje)
        elif periodo == 'mes':
            visitas = visitas.filter(data__year=hoje.year, data__month=hoje.month)
        elif periodo == 'ano':
            visitas = visitas.filter(data__year=hoje.year)
            
        context['todas_visitas'] = visitas
        
        # Visitas da barra lateral (sempre do dia selecionado no calendÃ¡rio)
        visitas_para_hoje = Visita.objects.filter(data=hoje).order_by('data', 'horario')
        if assessor_id and (user.is_superuser or getattr(user, 'is_admin', False)):
            visitas_para_hoje = visitas_para_hoje.filter(assessor_id=assessor_id)
        elif not (user.is_superuser or getattr(user, 'is_admin', False)):
            visitas_para_hoje = visitas_para_hoje.filter(assessor=user)
            
        context['visitas_hoje'] = visitas_para_hoje
        return context

class VisitaCreateView(LoginRequiredMixin, CreateView):
    model = Visita
    form_class = VisitaForm
    template_name = 'core/visita_form.html'
    success_url = reverse_lazy('core:agenda')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        import json
        user = self.request.user
        if getattr(user, 'is_admin', False) or user.is_superuser:
            empresas = Empresa.objects.all()
        else:
            from django.db.models import Q
            empresas = Empresa.objects.filter(Q(assessor=user) | Q(assessores_autorizados=user)).distinct()
        empresa_assessor_map = {e.id: e.assessor.id for e in empresas if e.assessor}
        context['empresa_assessor_map'] = json.dumps(empresa_assessor_map)
        context['is_edit'] = False
        return context

    def form_valid(self, form):
        user = self.request.user
        # Se for assessor criando, forÃ§a que ele seja o assessor da visita
        if not (user.is_superuser or getattr(user, 'is_admin', False)):
            form.instance.assessor = user
        return super().form_valid(form)

class VisitaUpdateView(AdminRequiredMixin, UpdateView):
    model = Visita
    form_class = VisitaForm
    template_name = 'core/visita_form.html'
    success_url = reverse_lazy('core:agenda')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        if getattr(user, 'is_admin', False) or user.is_superuser:
            empresas = Empresa.objects.all()
        else:
            from django.db.models import Q
            empresas = Empresa.objects.filter(Q(assessor=user) | Q(assessores_autorizados=user)).distinct()
        empresa_assessor_map = {e.id: e.assessor.id for e in empresas if e.assessor}
        context['empresa_assessor_map'] = json.dumps(empresa_assessor_map)
        context['is_edit'] = True

        # Mapa de auditoria de GPS
        visita = self.get_object()
        context['auditoria_checkin_lat'] = visita.checkin_lat or ''
        context['auditoria_checkin_lng'] = visita.checkin_lng or ''
        context['auditoria_empresa_lat'] = visita.empresa.latitude or ''
        context['auditoria_empresa_lng'] = visita.empresa.longitude or ''
        context['auditoria_empresa_nome'] = visita.empresa.nome
        context['justificativa_distancia'] = visita.justificativa_distancia or ''
        return context

class VisitaDeleteView(AdminRequiredMixin, DeleteView):
    model = Visita
    template_name = 'core/visita_confirm_delete.html'
    success_url = reverse_lazy('core:agenda')

class VisitasAPIView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        user = request.user
        assessor_id = request.GET.get('assessor')

        if user.is_superuser or getattr(user, 'is_admin', False):
            visitas = Visita.objects.all()
            if assessor_id:
                visitas = visitas.filter(assessor_id=assessor_id)
        else:
            # Mostramos no calendÃ¡rio SOMENTE as visitas marcadas especificamente para ele
            visitas = Visita.objects.filter(assessor=user)

        events = []
        for v in visitas:
            # Cores baseadas no status
            color = '#3788d8' # Azul padrao - Agendada
            if v.status == 'realizada':
                color = '#28a745' # Verde
            elif v.status == 'cancelada':
                color = '#dc3545' # Vermelho

            events.append({
                'id': v.id,
                'title': f"{v.empresa.nome} ({v.assessor.username})",
                'start': f"{v.data.isoformat()}T{v.horario.isoformat()}",
                'backgroundColor': color,
                'borderColor': color,
                'status': v.status,
                'assessor': v.assessor.username
            })
        
        return JsonResponse(events, safe=False)

# -- MÃ“DULO DO CONSULTOR (RELATÃ“RIO PWA/DESKTOP) --
class RelatorioVisitaView(LoginRequiredMixin, UpdateView):
    model = Visita
    form_class = RelatorioVisitaForm
    template_name = 'core/mobile/relatorio_form.html'
    success_url = reverse_lazy('core:agenda')

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or getattr(user, 'is_admin', False):
            return Visita.objects.all()
        return Visita.objects.filter(assessor=user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from .data_sources import resolver_opcoes
        perguntas = PerguntaRelatorio.objects.filter(ativa=True).order_by('id')
        respostas = {r.pergunta_id: r.resposta for r in self.object.respostas.all()}
        
        context_perguntas = []
        for p in perguntas:
            if p.tipo_resposta == 'lista_suspensa':
                # Se tem fonte de dados registrada, resolve dinamicamente
                if p.fonte_dados and p.fonte_dados != 'manual':
                    opcoes_list = resolver_opcoes(p.fonte_dados, self.object)
                else:
                    # Fonte manual: usa opcoes_resposta digitadas
                    opcoes_list = [opc.strip() for opc in p.opcoes_resposta.split(',')] if p.opcoes_resposta else []
            elif p.tipo_resposta == 'multipla_escolha':
                opcoes_list = [opc.strip() for opc in p.opcoes_resposta.split(',')] if p.opcoes_resposta else []
            else:
                opcoes_list = []

            resposta_salva = respostas.get(p.id, '')
            # Para lista_suspensa, a resposta salva Ã© "A, B, C" â€” convertemos para lista
            resposta_lista = [v.strip() for v in resposta_salva.split(',')] if (p.tipo_resposta == 'lista_suspensa' and resposta_salva) else []

            context_perguntas.append({
                'id': p.id,
                'texto': p.texto,
                'tipo_resposta': p.tipo_resposta,
                'opcoes_resposta': opcoes_list,
                'resposta': resposta_salva,
                'resposta_lista': resposta_lista,
            })
        
        context['perguntas'] = context_perguntas
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        from .models import VisitaFoto
        
        # Salvar as n fotos
        for f in self.request.FILES.getlist('fotos'):
            VisitaFoto.objects.create(visita=self.object, imagem=f)
            
        perguntas = PerguntaRelatorio.objects.filter(ativa=True)
        for p in perguntas:
            if p.tipo_resposta == 'lista_suspensa':
                # MÃºltipla seleÃ§Ã£o: getlist retorna lista de valores selecionados
                valores = self.request.POST.getlist(f'pergunta_{p.id}')
                resposta_texto = ', '.join(v for v in valores if v)
            else:
                resposta_texto = self.request.POST.get(f'pergunta_{p.id}', '')
            RespostaRelatorio.objects.update_or_create(
                visita=self.object,
                pergunta=p,
                defaults={'resposta': resposta_texto}
            )
        return response

# -- CRUD FUNCIONÃRIO --
class FuncionarioListView(LoginRequiredMixin, ListView):
    model = Funcionario
    template_name = 'core/funcionario_list.html'
    context_object_name = 'funcionarios'
    
    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user

        nome = self.request.GET.get('nome')
        empresa_id = self.request.GET.get('empresa')

        if nome:
            qs = qs.filter(nome__icontains=nome)
        if empresa_id:
            qs = qs.filter(empresa_id=empresa_id)

        if not (user.is_superuser or getattr(user, 'is_admin', False)):
            from django.db.models import Q
            qs = qs.filter(Q(empresa__assessor=user) | Q(empresa__visitas__assessor=user)).distinct()
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        if user.is_superuser or getattr(user, 'is_admin', False):
            context['empresas_list'] = Empresa.objects.all()
        else:
            from django.db.models import Q
            context['empresas_list'] = Empresa.objects.filter(Q(assessor=user) | Q(visitas__assessor=user)).distinct()
        return context


@login_required
def exportar_empresas(request, formato):
    formato = (formato or '').lower()
    if formato not in ['csv', 'xlsx', 'pdf']:
        messages.error(request, 'Formato de exportaÃ§Ã£o invÃ¡lido.')
        return redirect('core:empresa_list')

    # Reutiliza os mesmos filtros da listagem
    qs = Empresa.objects.select_related('assessor').all()
    user = request.user

    nome   = request.GET.get('nome')
    status = request.GET.get('status')
    cidade = request.GET.get('cidade')
    estado = request.GET.get('estado')
    assessor_id = request.GET.get('assessor')

    if nome:        qs = qs.filter(nome__icontains=nome)
    if status:      qs = qs.filter(status=status)
    if cidade:      qs = qs.filter(cidade__icontains=cidade)
    if estado:      qs = qs.filter(estado__iexact=estado)
    if assessor_id: qs = qs.filter(assessor_id=assessor_id)

    if not (user.is_superuser or getattr(user, 'is_admin', False)):
        from django.db.models import Q as _Q
        qs = qs.filter(_Q(assessor=user) | _Q(assessores_autorizados=user)).distinct()

    STATUS_MAP = {'A': 'Ativo', 'I': 'Inativo', 'N': 'Em NegociaÃ§Ã£o'}
    rows = [{
        'nome':      e.nome,
        'cnpj_cpf':  e.cnpj_cpf or '',
        'telefone':  e.telefone or '',
        'email':     e.email or '',
        'status':    STATUS_MAP.get(e.status, e.status),
        'assessor':  e.assessor.get_full_name() or e.assessor.username if e.assessor else '',
        'cidade':    e.cidade or '',
        'estado':    e.estado or '',
    } for e in qs]

    headers = ['nome', 'cnpj_cpf', 'telefone', 'email', 'status', 'assessor', 'cidade', 'estado']
    labels  = ['Nome', 'CNPJ/CPF', 'Telefone', 'E-mail', 'Status', 'Assessor', 'Cidade', 'Estado']

    if formato == 'csv':
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="empresas.csv"'
        response.write('\ufeff')  # BOM para Excel abrir corretamente
        writer = csv.writer(response)
        writer.writerow(labels)
        for r in rows:
            writer.writerow([r[h] for h in headers])
        return response

    if formato == 'xlsx':
        output = io.BytesIO()
        df = pd.DataFrame([{l: r[h] for l, h in zip(labels, headers)} for r in rows])
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Empresas')
        output.seek(0)
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="empresas.xlsx"'
        return response

    # PDF
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import landscape, A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet

    output = io.BytesIO()
    doc = SimpleDocTemplate(output, pagesize=landscape(A4),
                            leftMargin=20, rightMargin=20, topMargin=20, bottomMargin=20)
    styles = getSampleStyleSheet()
    story = [
        Paragraph('RelatÃ³rio de Empresas', styles['Title']),
        Spacer(1, 12),
    ]

    table_data = [labels]
    for r in rows:
        table_data.append([r[h] for h in headers])

    table = Table(table_data, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND',   (0, 0), (-1,  0), colors.HexColor('#2563EB')),
        ('TEXTCOLOR',    (0, 0), (-1,  0), colors.white),
        ('FONTNAME',     (0, 0), (-1,  0), 'Helvetica-Bold'),
        ('FONTSIZE',     (0, 0), (-1, -1), 8),
        ('GRID',         (0, 0), (-1, -1), 0.4, colors.grey),
        ('VALIGN',       (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
    ]))
    story.append(table)
    doc.build(story)
    output.seek(0)

    response = HttpResponse(output.read(), content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="empresas.pdf"'
    return response


def _funcionarios_queryset_export(request):
    qs = Funcionario.objects.select_related('empresa').all()
    user = request.user

    nome = request.GET.get('nome')
    empresa_id = request.GET.get('empresa')

    if nome:
        qs = qs.filter(nome__icontains=nome)
    if empresa_id:
        qs = qs.filter(empresa_id=empresa_id)

    if not (user.is_superuser or getattr(user, 'is_admin', False)):
        from django.db.models import Q
        qs = qs.filter(Q(empresa__assessor=user) | Q(empresa__visitas__assessor=user)).distinct()

    return qs


@login_required
def exportar_funcionarios(request, formato):
    formato = (formato or '').lower()
    if formato not in ['csv', 'xlsx', 'pdf']:
        messages.error(request, 'Formato de exportaÃ§Ã£o invÃ¡lido.')
        return redirect('core:funcionario_list')

    qs = _funcionarios_queryset_export(request)
    rows = [{
        'nome': f.nome,
        'empresa': f.empresa.nome if f.empresa else '',
        'departamento': f.departamento or '',
        'cargo': f.cargo or '',
        'telefone': f.telefone or '',
        'email': f.email or '',
    } for f in qs]

    if formato == 'csv':
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="funcionarios.csv"'
        response.write('\ufeff')
        writer = csv.writer(response)
        writer.writerow(['nome', 'empresa', 'departamento', 'cargo', 'telefone', 'email'])
        for r in rows:
            writer.writerow([r['nome'], r['empresa'], r['departamento'], r['cargo'], r['telefone'], r['email']])
        return response

    if formato == 'xlsx':
        output = io.BytesIO()
        df = pd.DataFrame(rows, columns=['nome', 'empresa', 'departamento', 'cargo', 'telefone', 'email'])
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Funcionarios')
        output.seek(0)
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="funcionarios.xlsx"'
        return response

    # PDF
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import landscape, A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet

    output = io.BytesIO()
    doc = SimpleDocTemplate(output, pagesize=landscape(A4), leftMargin=20, rightMargin=20, topMargin=20, bottomMargin=20)
    styles = getSampleStyleSheet()
    story = [
        Paragraph('RelatÃ³rio de FuncionÃ¡rios', styles['Title']),
        Spacer(1, 12),
    ]

    table_data = [['Nome', 'Empresa', 'Departamento', 'Cargo', 'Telefone', 'E-mail']]
    for r in rows:
        table_data.append([r['nome'], r['empresa'], r['departamento'], r['cargo'], r['telefone'], r['email']])

    table = Table(table_data, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563EB')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
    ]))
    story.append(table)
    doc.build(story)
    output.seek(0)

    response = HttpResponse(output.read(), content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="funcionarios.pdf"'
    return response

class FuncionarioCreateView(AdminRequiredMixin, CreateView):
    model = Funcionario
    form_class = FuncionarioForm
    template_name = 'core/funcionario_form.html'
    success_url = reverse_lazy('core:funcionario_list')

class FuncionarioUpdateView(LoginRequiredMixin, UpdateView):
    model = Funcionario
    form_class = FuncionarioForm
    template_name = 'core/funcionario_form.html'
    success_url = reverse_lazy('core:funcionario_list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        user = self.request.user
        if not (user.is_superuser or getattr(user, 'is_admin', False)):
            for field in form.fields.values():
                field.disabled = True
        return form

    def post(self, request, *args, **kwargs):
        user = request.user
        if not (user.is_superuser or getattr(user, 'is_admin', False)):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("Apenas administradores podem editar.")
        return super().post(request, *args, **kwargs)

class FuncionarioDeleteView(AdminRequiredMixin, DeleteView):
    model = Funcionario
    template_name = 'core/funcionario_confirm_delete.html'
    success_url = reverse_lazy('core:funcionario_list')

import traceback

@login_required
def importar_empresas(request):
    if not (request.user.is_superuser or getattr(request.user, 'is_admin', False)):
        messages.error(request, 'Sem permissÃ£o.')
        return redirect('core:empresa_list')

    if request.method == 'POST' and request.FILES.get('arquivo_importacao'):
        arquivo = request.FILES['arquivo_importacao']
        try:
            if arquivo.name.endswith('.csv'):
                df = pd.read_csv(arquivo, encoding='utf-8')
            elif arquivo.name.endswith('.xlsx'):
                df = pd.read_excel(arquivo)
            else:
                messages.error(request, "Formato nÃ£o suportado. Use .csv ou .xlsx")
                return redirect('core:empresa_list')
                
            required_cols = ['nome', 'telefone', 'email', 'status', 'assessor_username']
            # We allow assessor_username to be empty for some
            columns = df.columns.str.strip().str.lower()
            
            if not all(col in columns for col in required_cols):
                messages.error(request, f"Arquivo nÃ£o possui todas as colunas obrigatÃ³rias: {required_cols}")
                return redirect('core:empresa_list')
            
            sucesso = 0
            for index, row in df.iterrows():
                try:
                    nome_val = str(row['nome']).strip() if pd.notna(row['nome']) else ''
                    if not nome_val: continue

                    # Get assessor
                    username = str(row['assessor_username']).strip() if pd.notna(row['assessor_username']) else ''
                    assessor_obj = CustomUser.objects.filter(username=username, is_assessor=True).first() if username else None
                    
                    empresa, _ = Empresa.objects.update_or_create(
                        nome=nome_val,
                        defaults={
                            'cnpj_cpf': str(row['cnpj_cpf']).strip() if 'cnpj_cpf' in columns and pd.notna(row['cnpj_cpf']) else '',
                            'telefone': str(row['telefone']) if pd.notna(row['telefone']) else '',
                            'email': str(row['email']) if pd.notna(row['email']) else '',
                            'status': {
                                'ativo': 'A', 'inativo': 'I', 'em negociaÃ§Ã£o': 'N', 'em negociacao': 'N',
                                'a': 'A', 'i': 'I', 'n': 'N'
                            }.get(str(row['status']).strip().lower(), 'A') if pd.notna(row['status']) else 'A',
                            'assessor': assessor_obj,
                            'cep': str(row['cep']).strip() if 'cep' in columns and pd.notna(row['cep']) else '',
                            'rua': str(row['rua']).strip() if 'rua' in columns and pd.notna(row['rua']) else '',
                            'numero': str(row['numero']).strip() if 'numero' in columns and pd.notna(row['numero']) else '',
                            'bairro': str(row['bairro']).strip() if 'bairro' in columns and pd.notna(row['bairro']) else '',
                            'cidade': str(row['cidade']).strip() if 'cidade' in columns and pd.notna(row['cidade']) else '',
                            'estado': str(row['estado']).strip().upper() if 'estado' in columns and pd.notna(row['estado']) else '',
                            'latitude': str(row['latitude']).strip() if 'latitude' in columns and pd.notna(row['latitude']) else None,
                            'longitude': str(row['longitude']).strip() if 'longitude' in columns and pd.notna(row['longitude']) else None
                        }
                    )
                    if empresa.preencher_endereco_pelo_cep():
                        empresa.save(update_fields=['cep', 'rua', 'bairro', 'cidade', 'estado'])
                    sucesso += 1
                except Exception as e:
                    print(f"Erro linha {index}: {e}")
                    continue
            messages.success(request, f"{sucesso} empresas importadas com sucesso!")
        except Exception as e:
            traceback.print_exc()
            messages.error(request, f"Erro ao processar arquivo: {str(e)}")
            
    return redirect('core:empresa_list')

@login_required
def importar_funcionarios(request):
    if not (request.user.is_superuser or getattr(request.user, 'is_admin', False)):
        messages.error(request, 'Sem permissÃ£o.')
        return redirect('core:contato_list')

    if request.method == 'POST' and request.FILES.get('arquivo_importacao'):
        arquivo = request.FILES['arquivo_importacao']
        try:
            if arquivo.name.endswith('.csv'):
                df = pd.read_csv(arquivo, encoding='utf-8')
            elif arquivo.name.endswith('.xlsx'):
                df = pd.read_excel(arquivo)
            else:
                messages.error(request, "Formato nÃ£o suportado. Use .csv ou .xlsx")
                return redirect('core:contato_list')
                
            required_cols = ['nome', 'empresa', 'departamento', 'cargo', 'telefone', 'email']
            columns = df.columns.str.strip().str.lower()
            
            if not all(col in columns for col in required_cols):
                messages.error(request, f"Arquivo nÃ£o possui todas as colunas obrigatÃ³rias: {required_cols}")
                return redirect('core:contato_list')
            
            sucesso = 0
            for index, row in df.iterrows():
                try:
                    empresa_nome = str(row['empresa']).strip() if pd.notna(row['empresa']) else ''
                    if not empresa_nome: continue
                    
                    empresa_obj = Empresa.objects.filter(nome__icontains=empresa_nome).first()
                    if not empresa_obj:
                        continue # Skip if school not found
                        
                    nome_val = str(row['nome']).strip()
                    if not nome_val or nome_val == 'nan': continue
                    
                    Funcionario.objects.update_or_create(
                        nome=nome_val,
                        empresa=empresa_obj,
                        defaults={
                            'departamento': str(row['departamento']).strip() if pd.notna(row['departamento']) else '',
                            'cargo': str(row['cargo']).strip() if pd.notna(row['cargo']) else '',
                            'telefone': str(row['telefone']) if pd.notna(row['telefone']) else '',
                            'email': str(row['email']) if pd.notna(row['email']) else ''
                        }
                    )
                    
                    sucesso += 1
                except Exception as e:
                    print(f"Erro linha {index}: {e}")
                    continue
            messages.success(request, f"{sucesso} funcionÃ¡rios importados com sucesso!")
        except Exception as e:
            traceback.print_exc()
            messages.error(request, f"Erro ao processar arquivo: {str(e)}")
            
    return redirect('core:contato_list')

# -- MÃ“DULO DE PERGUNTAS (RELATÃ“RIO DE VISITA) --
class PerguntaListView(AdminRequiredMixin, ListView):
    model = PerguntaRelatorio
    template_name = 'core/pergunta_list.html'
    context_object_name = 'perguntas'

class PerguntaCreateView(AdminRequiredMixin, CreateView):
    model = PerguntaRelatorio
    form_class = PerguntaRelatorioForm
    template_name = 'core/pergunta_form.html'
    success_url = reverse_lazy('core:pergunta_list')

class PerguntaUpdateView(AdminRequiredMixin, UpdateView):
    model = PerguntaRelatorio
    form_class = PerguntaRelatorioForm
    template_name = 'core/pergunta_form.html'
    success_url = reverse_lazy('core:pergunta_list')

class PerguntaDeleteView(AdminRequiredMixin, DeleteView):
    model = PerguntaRelatorio
    template_name = 'core/pergunta_confirm_delete.html'
    success_url = reverse_lazy('core:pergunta_list')

# ==========================================
# MÃ“DULO DE PERMISSÃ•ES E GRUPOS
# ==========================================
class GroupListView(AdminRequiredMixin, ListView):
    model = Group
    template_name = 'core/group_list.html'
    context_object_name = 'grupos'

    def get_queryset(self):
        qs = super().get_queryset()
        nome = self.request.GET.get('nome')
        if nome:
            qs = qs.filter(name__icontains=nome)
        return qs

class GroupCreateView(AdminRequiredMixin, CreateView):
    model = Group
    form_class = GroupForm
    template_name = 'core/group_form.html'
    success_url = reverse_lazy('core:group_list')
    
    def form_valid(self, form):
        messages.success(self.request, "Grupo de permissÃµes criado com sucesso!")
        return super().form_valid(form)

class GroupUpdateView(AdminRequiredMixin, UpdateView):
    model = Group
    form_class = GroupForm
    template_name = 'core/group_form.html'
    success_url = reverse_lazy('core:group_list')

    def form_valid(self, form):
        messages.success(self.request, "Grupo de permissÃµes atualizado com sucesso!")
        return super().form_valid(form)

class GroupDeleteView(AdminRequiredMixin, DeleteView):
    model = Group
    template_name = 'core/group_confirm_delete.html'
    success_url = reverse_lazy('core:group_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Grupo excluÃ­do com sucesso.")
        return super().delete(request, *args, **kwargs)

# ==========================================
# MÃ“DULO DE USUÃRIOS ADMINISTRADORES
# ==========================================
class AdminUserListView(AdminRequiredMixin, ListView):
    model = CustomUser
    template_name = 'core/admin_user_list.html'
    context_object_name = 'usuarios'

    def get_queryset(self):
        qs = super().get_queryset().filter(is_admin=True)
        nome = self.request.GET.get('nome')
        if nome:
            qs = qs.filter(username__icontains=nome)
        return qs

class AdminUserCreateView(AdminRequiredMixin, CreateView):
    model = CustomUser
    form_class = AdminUserForm
    template_name = 'core/admin_user_form.html'
    success_url = reverse_lazy('core:admin_user_list')
    
    def form_valid(self, form):
        from django.db import transaction
        try:
            with transaction.atomic():
                response = super().form_valid(form)
        except IntegrityError:
            form.add_error("username", "JÃ¡ existe um usuÃ¡rio com esse nome de usuÃ¡rio.")
            return self.form_invalid(form)
        messages.success(self.request, "Administrador criado com sucesso!")
        return response
class AdminUserUpdateView(AdminRequiredMixin, UpdateView):
    model = CustomUser
    form_class = AdminUserForm
    template_name = 'core/admin_user_form.html'
    success_url = reverse_lazy('core:admin_user_list')

    def form_valid(self, form):
        from django.db import transaction
        try:
            with transaction.atomic():
                response = super().form_valid(form)
        except IntegrityError:
            form.add_error("username", "JÃ¡ existe um usuÃ¡rio com esse nome de usuÃ¡rio.")
            return self.form_invalid(form)
        messages.success(self.request, "Administrador atualizado com sucesso!")
        return response

class AdminUserDeleteView(AdminRequiredMixin, DeleteView):
    model = CustomUser
    template_name = 'core/admin_user_confirm_delete.html'
    success_url = reverse_lazy('core:admin_user_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Administrador excluÃ­do com sucesso.")
        return super().delete(request, *args, **kwargs)

@login_required
def download_modelo_empresas(request):
    import io
    from openpyxl import Workbook
    from openpyxl.worksheet.datavalidation import DataValidation
    from django.http import HttpResponse

    output = io.BytesIO()
    wb = Workbook()
    ws = wb.active
    ws.title = "Empresas"

    cols = [
        'nome', 'cnpj_cpf', 'telefone', 'email', 'status', 
        'assessor_username', 'cep', 'rua', 'numero', 'bairro', 
        'cidade', 'estado', 'latitude', 'longitude'
    ]
    
    ws.append(cols)
    
    # Exemplo
    ws.append([
        'Empresa Exemplo', '00.000.000/0001-00', '(11) 99999-9999', 'contato@exemplo.com', 'Ativo',
        'admin', '01001-000', 'PraÃ§a da SÃ©', '100', 'SÃ©', 'SÃ£o Paulo', 'SP', '-23.550520', '-46.633308'
    ])

    # ValidaÃ§Ã£o de Dados para a coluna Status (E)
    dv = DataValidation(type="list", formula1='"Ativo,Inativo,Em NegociaÃ§Ã£o"', allow_blank=True)
    dv.error = 'Escolha um status vÃ¡lido da lista'
    dv.errorTitle = 'Status InvÃ¡lido'
    dv.prompt = 'Escolha: Ativo, Inativo ou Em NegociaÃ§Ã£o'
    dv.promptTitle = 'Escolha o Status'

    ws.add_data_validation(dv)
    dv.add('E2:E1000')

    wb.save(output)
    output.seek(0)

    response = HttpResponse(
        output.read(), 
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="modelo_importacao_empresas.xlsx"'
    return response

@login_required
def download_modelo_funcionarios(request):
    import io
    from openpyxl import Workbook
    from django.http import HttpResponse

    output = io.BytesIO()
    wb = Workbook()
    ws = wb.active
    ws.title = "FuncionÃ¡rios"

    cols = ['nome', 'empresa', 'departamento', 'cargo', 'telefone', 'email']

    ws.append(cols)

    # Linha de exemplo
    ws.append([
        'JoÃ£o da Silva', 'Empresa Exemplo',
        'TI', 'Analista', '(11) 98888-7777', 'joao@exemplo.com'
    ])

    wb.save(output)
    output.seek(0)

    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="modelo_importacao_funcionarios.xlsx"'
    return response

