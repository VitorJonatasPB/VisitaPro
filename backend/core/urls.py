from django.urls import path
from . import views
from . import web_relatorios_views

app_name = 'core'

urlpatterns = [
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.custom_logout, name='logout'),
    
    # Dashboards
    path('admin-panel/', views.DashboardAdminView.as_view(), name='dashboard_admin'),
    path('assessor-panel/', views.DashboardAssessorView.as_view(), name='dashboard_assessor'),
    
    # Rota raiz redireciona para login
    path('', views.CustomLoginView.as_view(), name='index'),

    # PWA files
    path('manifest.json', views.ManifestView.as_view(), name='manifest'),
    path('serviceworker.js', views.ServiceWorkerView.as_view(), name='serviceworker'),


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

    # Assessor
    path('assessores/', views.AssessorListView.as_view(), name='assessor_list'),
    path('assessores/novo/', views.AssessorCreateView.as_view(), name='assessor_create'),
    path('assessores/<int:pk>/editar/', views.AssessorUpdateView.as_view(), name='assessor_update'),
    path('assessores/<int:pk>/excluir/', views.AssessorDeleteView.as_view(), name='assessor_delete'),

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

    # Configuração PWA (Mobile) - Convertido para Módulo do Assessor (Relatório)
    path('agenda/<int:pk>/relatorio/', views.RelatorioVisitaView.as_view(), name='visita_relatorio'),

    # Funcionários
    path('funcionarios/', views.FuncionarioListView.as_view(), name='funcionario_list'),
    path('funcionarios/novo/', views.FuncionarioCreateView.as_view(), name='funcionario_create'),
    path('funcionarios/<int:pk>/editar/', views.FuncionarioUpdateView.as_view(), name='funcionario_update'),
    path('funcionarios/<int:pk>/excluir/', views.FuncionarioDeleteView.as_view(), name='funcionario_delete'),

    # Relatórios Web
    path('relatorios/', web_relatorios_views.RelatorioListView.as_view(), name='listar_relatorios'),
    path('relatorios/novo/', web_relatorios_views.RelatorioCreateView.as_view(), name='novo_relatorio'),
    path('relatorios/<int:pk>/', web_relatorios_views.RelatorioDetailView.as_view(), name='view_relatorio'),
    path('relatorios/<int:pk>/download/', web_relatorios_views.RelatorioDownloadView.as_view(), name='download_relatorio'),
    path('relatorios/<int:pk>/deletar/', web_relatorios_views.RelatorioDeleteView.as_view(), name='delete_relatorio'),

    # Imports
    path('importar/empresas/', views.importar_empresas, name='importar_empresas'),
    path('importar/modelo/', views.download_modelo_empresas, name='download_modelo_empresas'),
    path('importar/funcionarios/', views.importar_funcionarios, name='importar_funcionarios'),
    path('importar/modelo-funcionarios/', views.download_modelo_funcionarios, name='download_modelo_funcionarios'),
    path('funcionarios/exportar/<str:formato>/', views.exportar_funcionarios, name='exportar_funcionarios'),
    path('empresas/exportar/<str:formato>/', views.exportar_empresas, name='exportar_empresas'),
]
