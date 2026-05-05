from django.core.management.base import BaseCommand
from django.db.models import Q

from core.models import Empresa


class Command(BaseCommand):
    help = "Preenche rua, bairro, cidade e estado das empresas usando o CEP."

    def add_arguments(self, parser):
        parser.add_argument(
            "--sobrescrever",
            action="store_true",
            help="Atualiza mesmo empresas que ja possuem parte do endereco preenchido.",
        )

    def handle(self, *args, **options):
        sobrescrever = options["sobrescrever"]

        empresas = Empresa.objects.exclude(cep__isnull=True).exclude(cep__exact="")
        if not sobrescrever:
            empresas = empresas.filter(
                Q(rua__isnull=True) | Q(rua__exact=""),
                Q(bairro__isnull=True) | Q(bairro__exact=""),
                Q(cidade__isnull=True) | Q(cidade__exact=""),
                Q(estado__isnull=True) | Q(estado__exact=""),
            )

        empresas = empresas.order_by("id")

        total = empresas.count()
        atualizadas = 0
        ignoradas = 0

        self.stdout.write(f"Empresas encontradas para revisar: {total}")

        for empresa in empresas:
            if empresa.preencher_endereco_pelo_cep(sobrescrever=sobrescrever):
                empresa.save(update_fields=["cep", "rua", "bairro", "cidade", "estado"])
                atualizadas += 1
                self.stdout.write(self.style.SUCCESS(f"Atualizada: {empresa.nome}"))
            else:
                ignoradas += 1
                self.stdout.write(self.style.WARNING(f"Ignorada: {empresa.nome}"))

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f"Atualizadas: {atualizadas}"))
        self.stdout.write(self.style.WARNING(f"Ignoradas: {ignoradas}"))
