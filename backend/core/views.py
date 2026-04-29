from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse_lazy
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DeleteView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import JsonResponse
import json
from django.conf import settings
from .models import Regiao, Empresa, Visita, CustomUser, Contato, Disciplina, PerguntaRelatorio, RespostaRelatorio
from .forms import RegiaoForm, ConsultorForm, AdminUserForm, EmpresaForm, VisitaForm, RelatorioVisitaForm, ContatoForm, DisciplinaForm, PerguntaRelatorioForm, GroupForm
from django.contrib.auth.models import Group
import pandas as pd
from django.contrib import messages

class CustomLoginView(LoginView):
    template_name = 'core/login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        user = self.request.user
        if getattr(user, 'is_admin', False) or user.is_superuser:
            return reverse_lazy('core:dashboard_admin')
        elif getattr(user, 'is_consultor', False):
            return reverse_lazy('core:dashboard_consultor')
        # Fallback para admin se for superuser sem os campos booleanos marcados
        if user.is_superuser:
            return reverse_lazy('core:dashboard_admin')
        return reverse_lazy('core:dashboard_consultor')

def custom_logout(request):
    logout(request)
    return redirect('core:login')

class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser or self.request.user.is_admin
        
class ConsultorRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_consultor

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

        # Filtro de Consultor
        consultor_id = self.request.GET.get('consultor_id')
        
        # Lista para o Select
        context['consultores_lista'] = CustomUser.objects.filter(is_consultor=True, is_active=True).order_by('first_name', 'username')
        context['consultor_id_selecionado'] = consultor_id
        
        # Consultor Atual e Iniciais
        iniciais = "TD"
        user_foto_url = None
        if consultor_id:
            try:
                consultor_obj = CustomUser.objects.get(id=int(consultor_id))
                if consultor_obj.first_name:
                    iniciais = consultor_obj.first_name[0].upper()
                    if consultor_obj.last_name:
                        iniciais += consultor_obj.last_name[0].upper()
                else:
                    iniciais = consultor_obj.username[:2].upper()
                user_foto_url = consultor_obj.foto.url if consultor_obj.foto else None
            except CustomUser.DoesNotExist:
                consultor_id = None
                user_foto_url = None
        
        context['user_initials'] = iniciais
        context['user_foto_url'] = user_foto_url
        
        # Filtrar as métricas gerais baseado ou não em consultor
        visitas_do_mes = Visita.objects.filter(data__year=ano_atual, data__month=mes_atual)
        if consultor_id:
            visitas_do_mes = visitas_do_mes.filter(consultor_id=consultor_id)
            
        context['agendadas_mes'] = visitas_do_mes.filter(status='agendada').count()
        context['visitas_realizadas_mes'] = visitas_do_mes.filter(status='realizada').count()
        context['canceladas_mes'] = visitas_do_mes.filter(status='cancelada').count()
        context['consultores_ativos'] = CustomUser.objects.filter(is_consultor=True, is_active=True).count()
        
        from django.db.models import Q
        empresas_qs = Empresa.objects.all()
        if consultor_id:
            empresas_qs = empresas_qs.filter(Q(consultor_id=consultor_id) | Q(visitas__consultor_id=consultor_id)).distinct()
        context['total_empresas'] = empresas_qs.count()
        
        from .models import Contato
        contatoes_qs = Contato.objects.all()
        if consultor_id:
            contatoes_qs = contatoes_qs.filter(empresa__in=empresas_qs).distinct()
        context['total_contatoes'] = contatoes_qs.count()
        
        # Últimas visitas
        ultimas_visitas = Visita.objects.all().order_by('-data', '-horario')
        if consultor_id:
            ultimas_visitas = ultimas_visitas.filter(consultor_id=consultor_id)
        context['ultimas_visitas'] = ultimas_visitas[:5]

        # Empresas no Mapa (se tiver filtro, mostra só as dele)
        from django.db.models import Q
        empresas = Empresa.objects.exclude(latitude__isnull=True).exclude(latitude__exact='').exclude(longitude__isnull=True).exclude(longitude__exact='')
        if consultor_id:
            empresas = empresas.filter(Q(consultor_id=consultor_id) | Q(visitas__consultor_id=consultor_id)).distinct()
            
        empresas_mapa = []
        for e in empresas:
            cor = e.consultor.cor_mapa if e.consultor and hasattr(e.consultor, 'cor_mapa') else '#3B82F6'
            nome_consultor = e.consultor.get_full_name() or e.consultor.username if e.consultor else 'Sem consultor'
            empresas_mapa.append({
                'nome': e.nome,
                'lat': e.latitude,
                'lng': e.longitude,
                'url': str(reverse_lazy('core:empresa_update', kwargs={'pk': e.id})),
                'cor': cor,
                'consultor': nome_consultor,
            })
        context['empresas_mapa'] = json.dumps(empresas_mapa)
        
        # Métrica p/ Gráfico de Colunas: Contatoes Atendidos nos últimos 6 meses
        grafico_labels = []
        grafico_data = []
        
        for i in range(4, -1, -1):
            mes = hoje.month - i
            ano = hoje.year
            if mes <= 0:
                mes += 12
                ano -= 1
                
            visitas_mes_ano = Visita.objects.filter(data__year=ano, data__month=mes, status='realizada')
            if consultor_id:
                visitas_mes_ano = visitas_mes_ano.filter(consultor_id=consultor_id)
                
            empresas_ids = set([v.empresa.id for v in visitas_mes_ano])
            from .models import Contato
            total_contatoes = Contato.objects.filter(empresa__id__in=empresas_ids).count()
            
            nome_mes = calendar.month_abbr[mes]
            meses_ptbr = {1:'Jan', 2:'Fev', 3:'Mar', 4:'Abr', 5:'Mai', 6:'Jun', 7:'Jul', 8:'Ago', 9:'Set', 10:'Out', 11:'Nov', 12:'Dez'}
            nome_mes_br = meses_ptbr.get(mes, '')
            
            grafico_labels.append(f"{nome_mes_br}/{str(ano)[-2:]}")
            grafico_data.append(total_contatoes)
            
        context['grafico_labels'] = json.dumps(grafico_labels)
        context['grafico_data'] = json.dumps(grafico_data)
        
        # Métrica p/ Gráfico de Rosca: % de Contatoes Atendidos no Total Geral
        # Para isso, precisamos ver todos os contatoes que já participaram de pelo menos 1 visita realizada
        import math
        visitas_para_rosca = Visita.objects.filter(status='realizada')
        if consultor_id:
            visitas_para_rosca = visitas_para_rosca.filter(consultor_id=consultor_id)
            
        contatoes_atendidos_ids = set()
        for v in visitas_para_rosca:
            for p in v.contatoes_atendidos.all():
                contatoes_atendidos_ids.add(p.id)
                
        total_atendidos_unicos = len(contatoes_atendidos_ids)
        total_contatoes_geral = context.get('total_contatoes', 0)
        
        if total_contatoes_geral > 0:
            porcentagem_atendidos = math.floor((total_atendidos_unicos / total_contatoes_geral) * 100)
        else:
            porcentagem_atendidos = 0
            
        porcentagem_nao_atendidos = 100 - porcentagem_atendidos
        
        context['rosca_atendidos'] = porcentagem_atendidos
        context['rosca_nao_atendidos'] = porcentagem_nao_atendidos
        context['total_atendidos_unicos'] = total_atendidos_unicos
        
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

# -- CRUD REGIÃO --
class RegiaoListView(AdminRequiredMixin, ListView):
    model = Regiao
    template_name = 'core/regiao_list.html'
    context_object_name = 'regioes'

    def get_queryset(self):
        qs = super().get_queryset()
        nome = self.request.GET.get('nome')
        secretaria = self.request.GET.get('secretaria')
        
        if nome:
            qs = qs.filter(nome__icontains=nome)
        if secretaria:
            qs = qs.filter(secretaria__icontains=secretaria)
            
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['secretarias_list'] = Regiao.objects.exclude(secretaria__isnull=True).exclude(secretaria__exact='').values_list('secretaria', flat=True).distinct().order_by('secretaria')
        return context

class RegiaoCreateView(AdminRequiredMixin, CreateView):
    model = Regiao
    form_class = RegiaoForm
    template_name = 'core/regiao_form.html'
    success_url = reverse_lazy('core:regiao_list')

class RegiaoUpdateView(AdminRequiredMixin, UpdateView):
    model = Regiao
    form_class = RegiaoForm
    template_name = 'core/regiao_form.html'
    success_url = reverse_lazy('core:regiao_list')

class RegiaoDeleteView(AdminRequiredMixin, DeleteView):
    model = Regiao
    template_name = 'core/regiao_confirm_delete.html'
    success_url = reverse_lazy('core:regiao_list')

class DashboardConsultorView(ConsultorRequiredMixin, TemplateView):
    template_name = 'core/dashboard_consultor.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        from django.db.models import Q
        empresas = Empresa.objects.filter(Q(consultor=user) | Q(visitas__consultor=user)).exclude(latitude__isnull=True).exclude(latitude__exact='').exclude(longitude__isnull=True).exclude(longitude__exact='').distinct()
        empresas_mapa = []
        for e in empresas:
            empresas_mapa.append({
                'nome': e.nome,
                'lat': e.latitude,
                'lng': e.longitude,
                'url': str(reverse_lazy('core:empresa_update', kwargs={'pk': e.id}))
            })
        context['empresas_mapa'] = json.dumps(empresas_mapa)
        
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
        
        # Filtros de Visitas do Mês para Consultor
        from django.utils import timezone
        import datetime
        import calendar
        
        hoje = timezone.now().date()
        mes_atual = hoje.month
        ano_atual = hoje.year
        
        visitas_do_consultor_mes = Visita.objects.filter(
            consultor=user, 
            data__year=ano_atual, 
            data__month=mes_atual
        )
        
        context['visitas_agendadas_mes'] = visitas_do_consultor_mes.filter(status='agendada').count()
        context['visitas_realizadas_mes'] = visitas_do_consultor_mes.filter(status='realizada').count()
        context['visitas_canceladas_mes'] = visitas_do_consultor_mes.filter(status='cancelada').count()
        
        # Manteve para caso seja usado em outro lugar no front
        context['proximas_visitas_mes'] = visitas_do_consultor_mes.filter(
            data__gte=hoje
        ).exclude(status='cancelada').count()
        
        context['visitas_hoje'] = Visita.objects.filter(
            consultor=user,
            data=hoje
        ).order_by('horario')
        
        context['total_empresas'] = empresas.count()
        from .models import Contato
        context['total_contatoes'] = Contato.objects.filter(empresa__in=empresas).distinct().count()
        
        # Métrica p/ Gráfico de Pizza: Contatoes Atendidos nos últimos 6 meses
        grafico_labels = []
        grafico_data = []
        
        # Começamos do mês atual caindo até 4 meses atrás (Total 5)
        for i in range(4, -1, -1):
            mes = hoje.month - i
            ano = hoje.year
            if mes <= 0:
                mes += 12
                ano -= 1
                
            # Buscar visitas 'realizadas' naquele mes/ano para o consultor
            visitas_mes_ano = Visita.objects.filter(consultor=user, data__year=ano, data__month=mes, status='realizada')
            
            # Pegar o ID de todas as empresas dessas visitas
            empresas_ids = set([v.empresa.id for v in visitas_mes_ano])
            
            # Contar total de contatoes dessas empresas
            from .models import Contato
            total_contatoes = Contato.objects.filter(empresa__id__in=empresas_ids).count()
            
            # Formatando o Nome do mes
            nome_mes = calendar.month_abbr[mes]  # ex: 'Jan', 'Feb' (Nota: por padrão pt-BR de locale, não tem no Django sem Babel, usaremos um mapa fixo p/ BR se preferível mas calendar é ok)
            meses_ptbr = {1:'Jan', 2:'Fev', 3:'Mar', 4:'Abr', 5:'Mai', 6:'Jun', 7:'Jul', 8:'Ago', 9:'Set', 10:'Out', 11:'Nov', 12:'Dez'}
            nome_mes_br = meses_ptbr.get(mes, '')
            
            grafico_labels.append(f"{nome_mes_br}/{str(ano)[-2:]}")
            grafico_data.append(total_contatoes)
            
        context['grafico_labels'] = json.dumps(grafico_labels)
        context['grafico_data'] = json.dumps(grafico_data)
        
        # Métrica p/ Gráfico de Rosca: % de Contatoes Atendidos no Total Geral do Consultor
        import math
        visitas_para_rosca = Visita.objects.filter(consultor=user, status='realizada')
        
        contatoes_atendidos_ids = set()
        for v in visitas_para_rosca:
            for p in v.contatoes_atendidos.all():
                contatoes_atendidos_ids.add(p.id)
                
        total_atendidos_unicos = len(contatoes_atendidos_ids)
        total_contatoes_geral = context.get('total_contatoes', 0)
        
        if total_contatoes_geral > 0:
            porcentagem_atendidos = math.floor((total_atendidos_unicos / total_contatoes_geral) * 100)
        else:
            porcentagem_atendidos = 0
            
        porcentagem_nao_atendidos = 100 - porcentagem_atendidos
        
        context['rosca_atendidos'] = porcentagem_atendidos
        context['rosca_nao_atendidos'] = porcentagem_nao_atendidos
        context['total_atendidos_unicos'] = total_atendidos_unicos
        
        return context

# -- CRUD CONSULTOR (USER) --
class ConsultorListView(AdminRequiredMixin, ListView):
    model = CustomUser
    template_name = 'core/consultor_list.html'
    context_object_name = 'consultores'
    
    def get_queryset(self):
        qs = CustomUser.objects.filter(is_consultor=True)
        nome = self.request.GET.get('nome')
        if nome:
            qs = qs.filter(first_name__icontains=nome) | qs.filter(username__icontains=nome)
        return qs

class ConsultorCreateView(AdminRequiredMixin, CreateView):
    model = CustomUser
    form_class = ConsultorForm
    template_name = 'core/consultor_form.html'
    success_url = reverse_lazy('core:consultor_list')

    def form_valid(self, form):
        # Antes de salvar no banco, definimos que este usuário É um consultor
        form.instance.is_consultor = True 
        return super().form_valid(form)

class ConsultorUpdateView(AdminRequiredMixin, UpdateView):
    model = CustomUser
    form_class = ConsultorForm
    template_name = 'core/consultor_form.html'
    success_url = reverse_lazy('core:consultor_list')

class ConsultorDeleteView(AdminRequiredMixin, DeleteView):
    model = CustomUser
    template_name = 'core/consultor_confirm_delete.html'
    success_url = reverse_lazy('core:consultor_list')

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
        regiao = self.request.GET.get('regiao')
        cidade = self.request.GET.get('cidade')
        status = self.request.GET.get('status')
        consultor_id = self.request.GET.get('consultor')

        if nome:
            qs = qs.filter(nome__icontains=nome)
        if regiao:
            qs = qs.filter(regiao_id=regiao)
        if cidade:
            qs = qs.filter(regiao__cidade__icontains=cidade)
        if status:
            qs = qs.filter(status=status)
        if consultor_id:
            qs = qs.filter(consultor_id=consultor_id)

        if not (user.is_superuser or getattr(user, 'is_admin', False)):
            # Retorna apenas as empresas que esse consultor está designado como titular ou autorizado
            from django.db.models import Q
            qs = qs.filter(Q(consultor=user) | Q(consultores_autorizados=user)).distinct()
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['regioes_list'] = Regiao.objects.all().order_name() if hasattr(Regiao.objects, 'order_name') else Regiao.objects.all().order_by('nome')
        context['cidades_list'] = Regiao.objects.exclude(cidade__isnull=True).exclude(cidade__exact='').values_list('cidade', flat=True).distinct().order_by('cidade')
        
        if user.is_superuser or getattr(user, 'is_admin', False):
            context['consultores_list'] = CustomUser.objects.filter(is_consultor=True)
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
        
        # Se for passado um status, filtremos para as de todo o mês atual
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
            qs = qs.filter(consultor=user)
            
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        import datetime
        from django.utils import timezone
        
        user = self.request.user
        
        data_alvo = getattr(self, 'data_alvo', None)
        if hasattr(self, 'status_filtro_ativo') and self.status_filtro_ativo:
            # Sendo status ativo, a exibição será mensal. Passaremos hoje apenas como base de calendário
            data_alvo = timezone.now().date()
            context['is_monthly_status'] = True
        else:
            context['is_monthly_status'] = False
            
        context['hoje'] = data_alvo
        context['dia_anterior'] = data_alvo - datetime.timedelta(days=1)
        context['proximo_dia'] = data_alvo + datetime.timedelta(days=1)
        
        # Obter a lista de dias que contém visitas atreladas a este usuário (Para o Flatpickr)
        if user.is_superuser or getattr(user, 'is_admin', False):
            visitas = Visita.objects.all()
        else:
            visitas = Visita.objects.filter(consultor=user)
        
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
        
        consultor_id = self.request.GET.get('consultor')
        
        if user.is_superuser or getattr(user, 'is_admin', False):
            context['consultores_list'] = CustomUser.objects.filter(is_consultor=True)
            visitas = Visita.objects.all().order_by('data', 'horario')
            if consultor_id:
                visitas = visitas.filter(consultor_id=consultor_id)
                context['consultor_id_selecionado'] = int(consultor_id)
        else:
            visitas = Visita.objects.filter(consultor=user).order_by('data', 'horario')
            
        periodo = self.request.GET.get('periodo', 'mes') # Por padrão foca no mês atual
        context['periodo'] = periodo
        
        if periodo == 'dia':
            visitas = visitas.filter(data=hoje)
        elif periodo == 'mes':
            visitas = visitas.filter(data__year=hoje.year, data__month=hoje.month)
        elif periodo == 'ano':
            visitas = visitas.filter(data__year=hoje.year)
            
        context['todas_visitas'] = visitas
        
        # Visitas da barra lateral (sempre do dia selecionado no calendário)
        visitas_para_hoje = Visita.objects.filter(data=hoje).order_by('data', 'horario')
        if consultor_id and (user.is_superuser or getattr(user, 'is_admin', False)):
            visitas_para_hoje = visitas_para_hoje.filter(consultor_id=consultor_id)
        elif not (user.is_superuser or getattr(user, 'is_admin', False)):
            visitas_para_hoje = visitas_para_hoje.filter(consultor=user)
            
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
            empresas = Empresa.objects.filter(Q(consultor=user) | Q(consultores_autorizados=user)).distinct()
        empresa_consultor_map = {e.id: e.consultor.id for e in empresas if e.consultor}
        context['empresa_consultor_map'] = json.dumps(empresa_consultor_map)
        context['is_edit'] = False
        return context

    def form_valid(self, form):
        user = self.request.user
        # Se for consultor criando, força que ele seja o consultor da visita
        if not (user.is_superuser or getattr(user, 'is_admin', False)):
            form.instance.consultor = user
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
            empresas = Empresa.objects.filter(Q(consultor=user) | Q(consultores_autorizados=user)).distinct()
        empresa_consultor_map = {e.id: e.consultor.id for e in empresas if e.consultor}
        context['empresa_consultor_map'] = json.dumps(empresa_consultor_map)
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
        consultor_id = request.GET.get('consultor')

        if user.is_superuser or getattr(user, 'is_admin', False):
            visitas = Visita.objects.all()
            if consultor_id:
                visitas = visitas.filter(consultor_id=consultor_id)
        else:
            # Mostramos no calendário SOMENTE as visitas marcadas especificamente para ele
            visitas = Visita.objects.filter(consultor=user)

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
                'title': f"{v.empresa.nome} ({v.consultor.username})",
                'start': f"{v.data.isoformat()}T{v.horario.isoformat()}",
                'backgroundColor': color,
                'borderColor': color,
                'status': v.status,
                'consultor': v.consultor.username
            })
        
        return JsonResponse(events, safe=False)

# -- MÓDULO DO CONSULTOR (RELATÓRIO PWA/DESKTOP) --
class RelatorioVisitaView(LoginRequiredMixin, UpdateView):
    model = Visita
    form_class = RelatorioVisitaForm
    template_name = 'core/mobile/relatorio_form.html'
    success_url = reverse_lazy('core:agenda')

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or getattr(user, 'is_admin', False):
            return Visita.objects.all()
        return Visita.objects.filter(consultor=user)

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
            # Para lista_suspensa, a resposta salva é "A, B, C" — convertemos para lista
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
                # Múltipla seleção: getlist retorna lista de valores selecionados
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

# -- CRUD CONTATO --
class ContatoListView(LoginRequiredMixin, ListView):
    model = Contato
    template_name = 'core/contato_list.html'
    context_object_name = 'contatoes'
    
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
            qs = qs.filter(Q(empresa__consultor=user) | Q(empresa__visitas__consultor=user)).distinct()
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        if user.is_superuser or getattr(user, 'is_admin', False):
            context['empresas_list'] = Empresa.objects.all()
        else:
            from django.db.models import Q
            context['empresas_list'] = Empresa.objects.filter(Q(consultor=user) | Q(visitas__consultor=user)).distinct()
        return context

class ContatoCreateView(AdminRequiredMixin, CreateView):
    model = Contato
    form_class = ContatoForm
    template_name = 'core/contato_form.html'
    success_url = reverse_lazy('core:contato_list')

class ContatoUpdateView(LoginRequiredMixin, UpdateView):
    model = Contato
    form_class = ContatoForm
    template_name = 'core/contato_form.html'
    success_url = reverse_lazy('core:contato_list')

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

class ContatoDeleteView(AdminRequiredMixin, DeleteView):
    model = Contato
    template_name = 'core/contato_confirm_delete.html'
    success_url = reverse_lazy('core:contato_list')

import traceback

@login_required
def importar_empresas(request):
    if not (request.user.is_superuser or getattr(request.user, 'is_admin', False)):
        messages.error(request, 'Sem permissão.')
        return redirect('core:empresa_list')

    if request.method == 'POST' and request.FILES.get('arquivo_importacao'):
        arquivo = request.FILES['arquivo_importacao']
        try:
            if arquivo.name.endswith('.csv'):
                df = pd.read_csv(arquivo, encoding='utf-8')
            elif arquivo.name.endswith('.xlsx'):
                df = pd.read_excel(arquivo)
            else:
                messages.error(request, "Formato não suportado. Use .csv ou .xlsx")
                return redirect('core:empresa_list')
                
            required_cols = ['nome', 'regiao', 'telefone', 'email', 'status', 'consultor_username']
            # We allow consultor_username to be empty for some
            columns = df.columns.str.strip().str.lower()
            
            if not all(col in columns for col in required_cols):
                messages.error(request, f"Arquivo não possui todas as colunas obrigatórias: {required_cols}")
                return redirect('core:empresa_list')
            
            sucesso = 0
            for index, row in df.iterrows():
                try:
                    regiao_nome = str(row['regiao']).strip() if pd.notna(row['regiao']) else ''
                    if not regiao_nome: continue
                    
                    # Create or get regiao
                    regiao_obj, _ = Regiao.objects.get_or_create(nome=regiao_nome, defaults={'cidade': 'Não informada'})
                    
                    # Get consultor
                    username = str(row['consultor_username']).strip() if pd.notna(row['consultor_username']) else ''
                    consultor_obj = CustomUser.objects.filter(username=username, is_consultor=True).first() if username else None
                    
                    Empresa.objects.update_or_create(
                        nome=str(row['nome']).strip(),
                        regiao=regiao_obj,
                        defaults={
                            'telefone': str(row['telefone']) if pd.notna(row['telefone']) else '',
                            'email': str(row['email']) if pd.notna(row['email']) else '',
                            'status': str(row['status']).strip().upper() if pd.notna(row['status']) else 'A',
                            'consultor': consultor_obj,
                            'latitude': str(row['latitude']).strip() if 'latitude' in columns and pd.notna(row['latitude']) else None,
                            'longitude': str(row['longitude']).strip() if 'longitude' in columns and pd.notna(row['longitude']) else None
                        }
                    )
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
def importar_contatoes(request):
    if not (request.user.is_superuser or getattr(request.user, 'is_admin', False)):
        messages.error(request, 'Sem permissão.')
        return redirect('core:contato_list')

    if request.method == 'POST' and request.FILES.get('arquivo_importacao'):
        arquivo = request.FILES['arquivo_importacao']
        try:
            if arquivo.name.endswith('.csv'):
                df = pd.read_csv(arquivo, encoding='utf-8')
            elif arquivo.name.endswith('.xlsx'):
                df = pd.read_excel(arquivo)
            else:
                messages.error(request, "Formato não suportado. Use .csv ou .xlsx")
                return redirect('core:contato_list')
                
            required_cols = ['nome', 'matricula', 'empresa', 'disciplinas', 'telefone', 'email']
            columns = df.columns.str.strip().str.lower()
            
            if not all(col in columns for col in required_cols):
                messages.error(request, f"Arquivo não possui todas as colunas obrigatórias: {required_cols}")
                return redirect('core:contato_list')
            
            sucesso = 0
            for index, row in df.iterrows():
                try:
                    empresa_nome = str(row['empresa']).strip() if pd.notna(row['empresa']) else ''
                    if not empresa_nome: continue
                    
                    empresa_obj = Empresa.objects.filter(nome__icontains=empresa_nome).first()
                    if not empresa_obj:
                        continue # Skip if school not found
                        
                    matricula_val = str(row['matricula']).strip() if pd.notna(row['matricula']) else ''
                    nome_val = str(row['nome']).strip()
                    if not nome_val or nome_val == 'nan': continue
                    
                    prof, created = Contato.objects.update_or_create(
                        nome=nome_val,
                        matricula=matricula_val,
                        empresa=empresa_obj,
                        defaults={
                            'telefone': str(row['telefone']) if pd.notna(row['telefone']) else '',
                            'email': str(row['email']) if pd.notna(row['email']) else ''
                        }
                    )
                    
                    disciplinas_str = str(row['disciplinas']) if pd.notna(row['disciplinas']) else ''
                    if disciplinas_str:
                        disc_list = [d.strip() for d in disciplinas_str.split(',') if d.strip()]
                        for d_nome in disc_list:
                            d_obj, _ = Disciplina.objects.get_or_create(nome=d_nome)
                            prof.disciplinas.add(d_obj)
                    sucesso += 1
                except Exception as e:
                    print(f"Erro linha {index}: {e}")
                    continue
            messages.success(request, f"{sucesso} contatoes importados com sucesso!")
        except Exception as e:
            traceback.print_exc()
            messages.error(request, f"Erro ao processar arquivo: {str(e)}")
            
    return redirect('core:contato_list')

# -- MÓDULO DE PERGUNTAS (RELATÓRIO DE VISITA) --
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
# MÓDULO DE PERMISSÕES E GRUPOS
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
        messages.success(self.request, "Grupo de permissões criado com sucesso!")
        return super().form_valid(form)

class GroupUpdateView(AdminRequiredMixin, UpdateView):
    model = Group
    form_class = GroupForm
    template_name = 'core/group_form.html'
    success_url = reverse_lazy('core:group_list')

    def form_valid(self, form):
        messages.success(self.request, "Grupo de permissões atualizado com sucesso!")
        return super().form_valid(form)

class GroupDeleteView(AdminRequiredMixin, DeleteView):
    model = Group
    template_name = 'core/group_confirm_delete.html'
    success_url = reverse_lazy('core:group_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Grupo excluído com sucesso.")
        return super().delete(request, *args, **kwargs)

# ==========================================
# MÓDULO DE USUÁRIOS ADMINISTRADORES
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
        messages.success(self.request, "Administrador criado com sucesso!")
        return super().form_valid(form)

class AdminUserUpdateView(AdminRequiredMixin, UpdateView):
    model = CustomUser
    form_class = AdminUserForm
    template_name = 'core/admin_user_form.html'
    success_url = reverse_lazy('core:admin_user_list')

    def form_valid(self, form):
        messages.success(self.request, "Administrador atualizado com sucesso!")
        return super().form_valid(form)

class AdminUserDeleteView(AdminRequiredMixin, DeleteView):
    model = CustomUser
    template_name = 'core/admin_user_confirm_delete.html'
    success_url = reverse_lazy('core:admin_user_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Administrador excluído com sucesso.")
        return super().delete(request, *args, **kwargs)
