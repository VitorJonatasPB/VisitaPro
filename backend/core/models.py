from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

class CustomUser(AbstractUser):
    is_consultor = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    foto = models.ImageField(upload_to='fotos_perfil/', null=True, blank=True)
    telefone = models.CharField(max_length=20, null=True, blank=True)
    cor_mapa = models.CharField(
        max_length=7, default='#3B82F6',
        help_text='Cor do pin no mapa (ex: #FF5733). Use um codigo hexadecimal.'
    )
    
    def __str__(self):
        return f"{self.username} ({self.get_full_name()})"

class Regiao(models.Model):
    nome = models.CharField(max_length=100, unique=True, verbose_name="Nome (CDE / DDZ)")
    cidade = models.CharField(max_length=100, verbose_name="Cidade")
    secretaria = models.CharField(max_length=150, blank=True, null=True, help_text="Ex: SEMED", verbose_name="Secretaria")
    
    class Meta:
        verbose_name = "CDE / DDZ"
        verbose_name_plural = "CDEs / DDZs"

    def __str__(self):
        return f"{self.nome} - {self.cidade}"

class Escola(models.Model):
    STATUS_CHOICES = [
        ('A', 'Ativa'),
        ('I', 'Inativa'),
    ]
    
    nome = models.CharField(max_length=150)
    regiao = models.ForeignKey(Regiao, on_delete=models.CASCADE, related_name='escolas', verbose_name="CDE / DDZ")
    telefone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    consultor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='escolas')
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    frequencia_recomendada_dias = models.PositiveIntegerField(default=30)
    consultores_autorizados = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='escolas_autorizadas', blank=True)
    ultima_visita = models.DateField(null=True, blank=True)
    latitude = models.CharField(max_length=50, blank=True, null=True, help_text="Ex: -23.550520")
    longitude = models.CharField(max_length=50, blank=True, null=True, help_text="Ex: -46.633308")
    
    def __str__(self):
        return self.nome

class Visita(models.Model):
    STATUS_CHOICES = [
        ('agendada', 'Agendada'),
        ('realizada', 'Realizada'),
        ('cancelada', 'Cancelada'),
    ]

    escola = models.ForeignKey(Escola, on_delete=models.CASCADE, related_name='visitas')
    consultor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='visitas')
    data = models.DateField()
    horario = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='agendada')
    observacoes = models.TextField(blank=True, null=True)
    relatorio = models.TextField(blank=True, null=True, help_text="Relatório preenchido pelo consultor")
    nome_responsavel = models.CharField(max_length=200, blank=True, null=True, help_text="Nome do responsável que assinou")
    assinatura = models.TextField(blank=True, null=True, help_text="Assinatura digitalizada em Base64")
    professores_atendidos = models.ManyToManyField('Professor', related_name='visitas_participadas', blank=True)
    
    checkin_time = models.DateTimeField(blank=True, null=True)
    checkin_lat = models.CharField(max_length=50, blank=True, null=True)
    checkin_lng = models.CharField(max_length=50, blank=True, null=True)
    
    checkout_time = models.DateTimeField(blank=True, null=True)
    checkout_lat = models.CharField(max_length=50, blank=True, null=True)
    checkout_lng = models.CharField(max_length=50, blank=True, null=True)

    sync_offline_flag = models.BooleanField(default=False, help_text="Sincronizado via cache offline")
    justificativa_distancia = models.TextField(blank=True, null=True, help_text="Justificativa do Check-in fora do raio")

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-data', '-horario']

    def __str__(self):
        return f"Visita {self.escola.nome} - {self.data} ({self.consultor.username})"

class VisitaFoto(models.Model):
    visita = models.ForeignKey(Visita, on_delete=models.CASCADE, related_name='fotos')
    imagem = models.ImageField(upload_to='visitas_fotos/')
    data_upload = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Foto da Visita {self.visita.id}"

class LogAlteracao(models.Model):
    visita = models.ForeignKey(Visita, on_delete=models.CASCADE, related_name='logs')
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='logs_gerados')
    data = models.DateTimeField(auto_now_add=True)
    descricao = models.TextField()

    def __str__(self):
        return f"Log {self.visita.id} por {self.usuario} em {self.data}"

class Disciplina(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    
    def __str__(self):
        return self.nome

class Professor(models.Model):
    nome = models.CharField(max_length=150)
    matricula = models.CharField(max_length=50, blank=True, null=True, verbose_name="Matrícula")
    escola = models.ForeignKey(Escola, on_delete=models.CASCADE, related_name='professores')
    disciplinas = models.ManyToManyField(Disciplina, related_name='professores', blank=True)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Professores"
        
    def __str__(self):
        return f"{self.nome} ({self.matricula})" if self.matricula else self.nome

class PerguntaRelatorio(models.Model):
    TIPO_CHOICES = [
        ('texto', 'Texto Curto'),
        ('texto_longo', 'Texto Longo'),
        ('data', 'Data (Calendário)'),
        ('booleano', 'Sim / Não'),
        ('numero', 'Número'),
        ('multipla_escolha', 'Múltipla Escolha (Opções)'),
        ('lista_suspensa', 'Lista Suspensa'),
    ]

    texto = models.CharField(max_length=255, help_text="Ex: A escola estava com as apostilas em dia?")
    tipo_resposta = models.CharField(max_length=30, choices=TIPO_CHOICES, default='texto')
    opcoes_resposta = models.CharField(max_length=500, blank=True, null=True, help_text="Para Múltipla Escolha ou Lista Suspensa manual. Separe por vírgula.")
    fonte_dados = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Apenas para Lista Suspensa. Chave da fonte registrada em data_sources.py (ex: 'professores'). Deixe em branco para opções manuais."
    )
    ativa = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.texto

class RespostaRelatorio(models.Model):
    visita = models.ForeignKey(Visita, on_delete=models.CASCADE, related_name='respostas')
    pergunta = models.ForeignKey(PerguntaRelatorio, on_delete=models.CASCADE)
    resposta = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('visita', 'pergunta')

    def __str__(self):
        return f"Resposta de Visita {self.visita.id} - Pergunta: {self.pergunta.texto}"

class BugReport(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    descricao = models.TextField(help_text="Descrição do erro reportado pelo usuário")
    device_info = models.CharField(max_length=255, blank=True, null=True, help_text="Informações do aparelho/OS")
    resolvido = models.BooleanField(default=False)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-criado_em']

    def __str__(self):
        status = "Resolvido" if self.resolvido else "Pendente"
        return f"Bug #{self.id} reportado por {self.usuario} - {status}"
