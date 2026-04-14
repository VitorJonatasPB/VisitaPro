from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.custom_logout, name='logout'),
    
    # Dashboards
    path('admin-panel/', views.DashboardAdminView.as_view(), name='dashboard_admin'),
    path('consultor-panel/', views.DashboardConsultorView.as_view(), name='dashboard_consultor'),
    
    # Rota raiz redireciona para login
    path('', views.CustomLoginView.as_view(), name='index'),

    # PWA files
    path('manifest.json', views.ManifestView.as_view(), name='manifest'),
    path('serviceworker.js', views.ServiceWorkerView.as_view(), name='serviceworker'),

    # Região
    path('regioes/', views.RegiaoListView.as_view(), name='regiao_list'),
    path('regioes/nova/', views.RegiaoCreateView.as_view(), name='regiao_create'),
    path('regioes/<int:pk>/editar/', views.RegiaoUpdateView.as_view(), name='regiao_update'),
    path('regioes/<int:pk>/excluir/', views.RegiaoDeleteView.as_view(), name='regiao_delete'),

    # Grupos (Novo Módulo de Permissões)
    path('grupos/', views.GroupListView.as_view(), name='group_list'),
    path('grupos/novo/', views.GroupCreateView.as_view(), name='group_create'),
    path('grupos/<int:pk>/editar/', views.GroupUpdateView.as_view(), name='group_update'),
    path('grupos/<int:pk>/excluir/', views.GroupDeleteView.as_view(), name='group_delete'),

    # Usuarios Administradores (Módulo de Permissões)
    path('administradores/', views.AdminUserListView.as_view(), name='admin_user_list'),
    path('administradores/novo/', views.AdminUserCreateView.as_view(), name='admin_user_create'),
    path('administradores/<int:pk>/editar/', views.AdminUserUpdateView.as_view(), name='admin_user_update'),
    path('administradores/<int:pk>/excluir/', views.AdminUserDeleteView.as_view(), name='admin_user_delete'),

    # Consultor
    path('consultores/', views.ConsultorListView.as_view(), name='consultor_list'),
    path('consultores/novo/', views.ConsultorCreateView.as_view(), name='consultor_create'),
    path('consultores/<int:pk>/editar/', views.ConsultorUpdateView.as_view(), name='consultor_update'),
    path('consultores/<int:pk>/excluir/', views.ConsultorDeleteView.as_view(), name='consultor_delete'),

    # Escola
    path('escolas/', views.EscolaListView.as_view(), name='escola_list'),
    path('escolas/nova/', views.EscolaCreateView.as_view(), name='escola_create'),
    path('escolas/<int:pk>/editar/', views.EscolaUpdateView.as_view(), name='escola_update'),
    path('escolas/<int:pk>/excluir/', views.EscolaDeleteView.as_view(), name='escola_delete'),

    # Agenda / Visitas
    path('agenda/', views.AgendaView.as_view(), name='agenda'),
    path('visitas/', views.VisitaListView.as_view(), name='visita_list'),
    path('agenda/nova-visita/', views.VisitaCreateView.as_view(), name='visita_create'),
    path('agenda/<int:pk>/editar/', views.VisitaUpdateView.as_view(), name='visita_update'),
    path('agenda/<int:pk>/excluir/', views.VisitaDeleteView.as_view(), name='visita_delete'),
    path('api/visitas/', views.VisitasAPIView.as_view(), name='api_visitas'),

    # Perguntas (Formulário Dinâmico)
    path('perguntas/', views.PerguntaListView.as_view(), name='pergunta_list'),
    path('perguntas/nova/', views.PerguntaCreateView.as_view(), name='pergunta_create'),
    path('perguntas/<int:pk>/editar/', views.PerguntaUpdateView.as_view(), name='pergunta_update'),
    path('perguntas/<int:pk>/excluir/', views.PerguntaDeleteView.as_view(), name='pergunta_delete'),

    # Configuração PWA (Mobile) - Convertido para Módulo do Consultor (Relatório)
    path('agenda/<int:pk>/relatorio/', views.RelatorioVisitaView.as_view(), name='visita_relatorio'),

    # Professor
    path('professores/', views.ProfessorListView.as_view(), name='professor_list'),
    path('professores/novo/', views.ProfessorCreateView.as_view(), name='professor_create'),
    path('professores/<int:pk>/editar/', views.ProfessorUpdateView.as_view(), name='professor_update'),
    path('professores/<int:pk>/excluir/', views.ProfessorDeleteView.as_view(), name='professor_delete'),

    # Imports
    path('importar/escolas/', views.importar_escolas, name='importar_escolas'),
    path('importar/professores/', views.importar_professores, name='importar_professores'),
]
