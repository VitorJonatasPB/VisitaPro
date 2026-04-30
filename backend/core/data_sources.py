"""
data_sources.py
---------------
Registro central de fontes de dados para o tipo "Lista Suspensa" das perguntas do formulário.

Para adicionar uma nova tabela/fonte:
1. Importe o model necessário
2. Adicione uma nova entrada em DATA_SOURCES
Nenhuma migração ou alteração de model/form é necessária.
"""

from .models import Funcionario


DATA_SOURCES = {
    "funcionarios": {
        "label": "Funcionários da Empresa",
        "resolver": lambda visita: list(
            Funcionario.objects.filter(empresa=visita.empresa).values_list(
                "nome", flat=True
            )
        ),
    },
    # Exemplo de como adicionar futuras fontes:
    # 'disciplinas': {
    #     'label': 'Disciplinas',
    #     'resolver': lambda visita: list(Disciplina.objects.values_list('nome', flat=True)),
    # },
}


def get_data_source_choices():
    """Retorna as choices (key, label) para o admin escolher a fonte de dados."""
    return [("manual", "Opções manuais (eu digito)")] + [
        (key, val["label"]) for key, val in DATA_SOURCES.items()
    ]


def resolver_opcoes(fonte_dados, visita):
    """
    Retorna a lista de strings de opções resolvida para uma visita específica.
    Retorna [] se a fonte for manual (a view usará opcoes_resposta diretamente).
    """
    if not fonte_dados or fonte_dados == "manual":
        return []
    source = DATA_SOURCES.get(fonte_dados)
    if source:
        try:
            return list(source["resolver"](visita))
        except Exception:
            return []
    return []
