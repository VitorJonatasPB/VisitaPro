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

    # Empresa
    path('empresas/', views.EmpresaListView.as_view(), name='empresa_list'),
    path('empresas/nova/', views.EmpresaCreateView.as_view(), name='empresa_create'),
    path('empresas/<int:pk>/editar/', views.EmpresaUpdateView.as_view(), name='empresa_update'),
    path('empresas/<int:pk>/excluir/', views.EmpresaDeleteView.as_view(), name='empresa_delete'),

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

    # Contato
    path('contatoes/', views.ContatoListView.as_view(), name='contato_list'),
    path('contatoes/novo/', views.ContatoCreateView.as_view(), name='contato_create'),
    path('contatoes/<int:pk>/editar/', views.ContatoUpdateView.as_view(), name='contato_update'),
    path('contatoes/<int:pk>/excluir/', views.ContatoDeleteView.as_view(), name='contato_delete'),

    # Imports
    path('importar/empresas/', views.importar_empresas, name='importar_empresas'),
    path('importar/contatoes/', views.importar_contatoes, name='importar_contatoes'),
]
