from django.urls import path
from . import api_views

urlpatterns = [
    # Agenda do consultor (visitas do dia)
    path('visitas/agenda/', api_views.agenda_hoje, name='api-agenda'),

    # Agenda do consultor (visitas do mês)
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
    path('visitas/<int:visita_id>/contatoes/', api_views.contatoes_empresa, name='api-contatoes'),

    # Meu Perfil e Bugs
    path('users/me/', api_views.meu_perfil, name='api-meu-perfil'),
    path('bugs/', api_views.reportar_bug, name='api-reportar-bug'),

    # Listagem global do consultor
    path('empresas/', api_views.lista_empresas, name='api-lista-empresas'),
    path('contatoes/', api_views.lista_contatoes, name='api-lista-contatoes'),
]
