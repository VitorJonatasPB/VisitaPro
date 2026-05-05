from django.urls import path
from . import api_views

urlpatterns = [
    # Agenda do assessor (visitas do dia)
    path('visitas/agenda/', api_views.agenda_hoje, name='api-agenda'),

    # Agenda do assessor (visitas do mês)
    path('visitas/mes/', api_views.agenda_mes, name='api-agenda-mes'),

    # Detalhe de uma visita específica
    path('visitas/<int:visita_id>/', api_views.detalhe_visita, name='api-detalhe-visita'),

    # Criação de novo agendamento
    path('visitas/novo/', api_views.criar_agendamento, name='api-novo-agendamento'),

    # Perguntas do relatório
    path('perguntas/', api_views.perguntas_ativas, name='api-perguntas'),

    # Check-in / Check-out / Relatório por visita
    path('visitas/calendario/', api_views.calendario_visitas, name='api-calendario'),
    path('visitas/<int:visita_id>/checkin/', api_views.fazer_checkin, name='api-checkin'),
    path('visitas/<int:visita_id>/checkout/', api_views.fazer_checkout, name='api-checkout'),
    path('visitas/<int:visita_id>/responder/', api_views.enviar_relatorio, name='api-responder'),
    path('visitas/<int:visita_id>/funcionarios/', api_views.funcionarios_empresa, name='api-funcionarios'),

    # Meu Perfil e Bugs
    path('users/me/', api_views.meu_perfil, name='api-meu-perfil'),
    path('bugs/', api_views.reportar_bug, name='api-reportar-bug'),

    # Listagem global do assessor e cadastros
    path('empresas/', api_views.lista_empresas, name='api-lista-empresas'),
    path('empresas/nova/', api_views.criar_empresa, name='api-nova-empresa'),
    path('funcionarios/', api_views.lista_funcionarios, name='api-lista-funcionarios'),
    path('funcionarios/novo/', api_views.criar_funcionario, name='api-novo-funcionario'),

    # Jornada Diária
    path('jornada/status/', api_views.status_jornada, name='api-status-jornada'),
    path('jornada/iniciar/', api_views.iniciar_jornada, name='api-iniciar-jornada'),
    path('jornada/sincronizar/', api_views.sincronizar_jornada, name='api-sincronizar-jornada'),
    path('jornada/finalizar/', api_views.finalizar_jornada, name='api-finalizar-jornada'),
]
