"""
URLs para o sistema de relatórios do VisitaPro.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .relatorios_views import (
    ConfiguracaoRelatorioViewSet,
    RelatorioGeradoViewSet,
    TemplatePessoalizadoViewSet
)

app_name = 'relatorios'

router = DefaultRouter()
router.register(r'configuracao', ConfiguracaoRelatorioViewSet, basename='configuracao-relatorio')
router.register(r'gerados', RelatorioGeradoViewSet, basename='relatorio-gerado')
router.register(r'templates', TemplatePessoalizadoViewSet, basename='template-personalizado')

urlpatterns = [
    path('', include(router.urls)),
]
