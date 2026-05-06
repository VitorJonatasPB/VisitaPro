from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.db.models.signals import m2m_changed
from django.dispatch import receiver
import requests

class CustomUser(AbstractUser):
    is_assessor = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    foto = models.ImageField(upload_to='fotos_perfil/', null=True, blank=True)

    telefone = models.CharField(max_length=20, null=True, blank=True)
    cor_mapa = models.CharField(
        max_length=7, default='#3B82F6',
        help_text='Cor do pin no mapa (ex: #FF5733). Use um codigo hexadecimal.'
    )
    
    def __str__(self):
        return f"{self.username} ({self.get_full_name()})"
        
    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"

class Empresa(models.Model):
    STATUS_CHOICES = [
        ('A', 'Ativa'),
        ('I', 'Inativa'),
        ('N', 'Em Negociação'),
    ]
    
    nome = models.CharField(max_length=150)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    cnpj_cpf = models.CharField(max_length=18, blank=True, null=True, verbose_name="CNPJ/CPF")
    assessor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='empresas')
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    assessores_autorizados = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='empresas_autorizadas', blank=True)
    ultima_visita = models.DateField(null=True, blank=True)
    cep = models.CharField(max_length=10, blank=True, null=True, verbose_name="CEP")
    rua = models.CharField(max_length=255, blank=True, null=True, verbose_name="Rua")
    numero = models.CharField(max_length=20, blank=True, null=True, verbose_name="Número")
    bairro = models.CharField(max_length=100, blank=True, null=True, verbose_name="Bairro")
    cidade = models.CharField(max_length=100, blank=True, null=True, verbose_name="Cidade")
    estado = models.CharField(max_length=2, blank=True, null=True, verbose_name="Estado")
    latitude = models.CharField(max_length=50, blank=True, null=True, help_text="Ex: -23.550520")
    longitude = models.CharField(max_length=50, blank=True, null=True, help_text="Ex: -46.633308")
    data_conversao = models.DateField(null=True, blank=True, verbose_name="Data de Conversão", help_text="Data em que a empresa passou de 'Em Negociação' para 'Ativa'")
    
    class Meta:
        verbose_name = "Empresa"
        verbose_name_plural = "Empresas"

    def __str__(self):
        return self.nome

    def save(self, *args, **kwargs):
        if not self.latitude or not self.longitude:
            self.geocodificar_pelo_google()
            
        # Rastreamento de conversão: se está mudando de 'N' para 'A'
        if self.pk:
            try:
                old_instance = Empresa.objects.get(pk=self.pk)
                if old_instance.status == 'N' and self.status == 'A':
                    from django.utils import timezone
                    self.data_conversao = timezone.now().date()
            except Empresa.DoesNotExist:
                pass
                
        super().save(*args, **kwargs)

    def preencher_endereco_pelo_cep(self, sobrescrever=False):
        cep_limpo = "".join(ch for ch in (self.cep or "") if ch.isdigit())
        if len(cep_limpo) != 8:
            return False

        if not sobrescrever and any([self.rua, self.bairro, self.cidade, self.estado]):
            return False

        try:
            response = requests.get(f"https://viacep.com.br/ws/{cep_limpo}/json/", timeout=5)
            response.raise_for_status()
            data = response.json()
        except Exception:
            return False

        if data.get("erro"):
            return False

        self.cep = f"{cep_limpo[:5]}-{cep_limpo[5:]}"
        self.rua = (data.get("logradouro") or "").strip()
        self.bairro = (data.get("bairro") or "").strip()
        self.cidade = (data.get("localidade") or "").strip()
        self.estado = (data.get("uf") or "").strip().upper()
        return True

    def geocodificar_pelo_google(self):
        from django.conf import settings
        
        api_key = getattr(settings, 'GOOGLE_MAPS_API_KEY', None)
        if not api_key:
            return

        partes = []
        if self.rua: 
            r = self.rua
            if self.numero: r += f", {self.numero}"
            partes.append(r)
        if self.cidade: partes.append(self.cidade)
        if self.estado: partes.append(self.estado)
        partes.append("Brasil")
        
        query = ", ".join(partes)
        
        if not partes or len(partes) <= 1:
            if self.cep:
                query = self.cep
            else:
                return

        try:
            url = f"https://maps.googleapis.com/maps/api/geocode/json?address={query}&key={api_key}"
            response = requests.get(url, timeout=5)
            data = response.json()
            
            if data['status'] == 'OK':
                location = data['results'][0]['geometry']['location']
                self.latitude = str(location['lat'])
                self.longitude = str(location['lng'])
                print(f"[GOOGLE API] Sucesso: {self.nome} -> {self.latitude}, {self.longitude}")
            else:
                print(f"[GOOGLE API] Erro ou nada encontrado para {self.nome}: {data['status']}")
        except Exception as e:
            print(f"[GOOGLE API] Falha na requisição para {self.nome}: {e}")

class Visita(models.Model):
    STATUS_CHOICES = [
        ('agendada', 'Agendada'),
        ('realizada', 'Realizada'),
        ('cancelada', 'Cancelada'),
    ]

    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='visitas')
    assessor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='visitas')
    data = models.DateField()
    horario = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='agendada')
    observacoes = models.TextField(blank=True, null=True)
    relatorio = models.TextField(blank=True, null=True, help_text="Relatório preenchido pelo consultor")
    nome_responsavel = models.CharField(max_length=200, blank=True, null=True, help_text="Nome do responsável que assinou")
    assinatura = models.TextField(blank=True, null=True, help_text="Assinatura digitalizada em Base64")
    contatoes_atendidos = models.ManyToManyField('Funcionario', related_name='visitas_participadas', blank=True)
    
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
        verbose_name = "Visita"
        verbose_name_plural = "Visitas"

    def __str__(self):
        return f"Visita {self.empresa.nome} - {self.data} ({self.assessor.username})"

class VisitaFoto(models.Model):
    visita = models.ForeignKey(Visita, on_delete=models.CASCADE, related_name='fotos')
    imagem = models.ImageField(upload_to='visitas_fotos/')
    data_upload = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Foto da Visita"
        verbose_name_plural = "Fotos das Visitas"

    def __str__(self):
        return f"Foto da Visita {self.visita.id}"

class LogAlteracao(models.Model):
    visita = models.ForeignKey(Visita, on_delete=models.CASCADE, related_name='logs')
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='logs_gerados')
    data = models.DateTimeField(auto_now_add=True)
    descricao = models.TextField()

    class Meta:
        verbose_name = "Log de Alteração"
        verbose_name_plural = "Logs de Alteração"

    def __str__(self):
        return f"Log {self.visita.id} por {self.usuario} em {self.data}"


class Funcionario(models.Model):
    nome = models.CharField(max_length=150)
    matricula = models.CharField(max_length=50, blank=True, null=True, verbose_name="Matrícula")
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='funcionarios')
    departamento = models.CharField(max_length=100, blank=True, null=True)
    cargo = models.CharField(max_length=100, blank=True, null=True)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Funcionário"
        verbose_name_plural = "Funcionários"
        db_table = 'core_funcionario'  # Nome padronizado da tabela no banco
        
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

    texto = models.CharField(max_length=255, help_text="Ex: A empresa estava com as apostilas em dia?")
    tipo_resposta = models.CharField(max_length=30, choices=TIPO_CHOICES, default='texto')
    opcoes_resposta = models.CharField(max_length=500, blank=True, null=True, help_text="Para Múltipla Escolha ou Lista Suspensa manual. Separe por vírgula.")
    fonte_dados = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Apenas para Lista Suspensa. Chave da fonte registrada em data_sources.py (ex: 'contatoes'). Deixe em branco para opções manuais."
    )
    ativa = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Pergunta do Relatório"
        verbose_name_plural = "Perguntas do Relatório"

    def __str__(self):
        return self.texto

class RespostaRelatorio(models.Model):
    visita = models.ForeignKey(Visita, on_delete=models.CASCADE, related_name='respostas')
    pergunta = models.ForeignKey(PerguntaRelatorio, on_delete=models.CASCADE)
    resposta = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('visita', 'pergunta')
        verbose_name = "Resposta do Relatório"
        verbose_name_plural = "Respostas do Relatório"

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
        verbose_name = "Relatório de Bug"
        verbose_name_plural = "Relatórios de Bug"

    def __str__(self):
        status = "Resolvido" if self.resolvido else "Pendente"
        return f"Bug #{self.id} reportado por {self.usuario} - {status}"

class Jornada(models.Model):
    assessor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='jornadas')
    data = models.DateField(auto_now_add=True)
    inicio_time = models.DateTimeField(auto_now_add=True)
    inicio_lat = models.CharField(max_length=50, blank=True, null=True)
    inicio_lng = models.CharField(max_length=50, blank=True, null=True)
    fim_time = models.DateTimeField(blank=True, null=True)
    fim_lat = models.CharField(max_length=50, blank=True, null=True)
    fim_lng = models.CharField(max_length=50, blank=True, null=True)
    km_total = models.FloatField(default=0.0, help_text="Quilometragem total percorrida no dia")
    status = models.CharField(max_length=20, choices=[('em_andamento', 'Em Andamento'), ('finalizada', 'Finalizada')], default='em_andamento')

    class Meta:
        verbose_name = "Jornada"
        verbose_name_plural = "Jornadas"

    def __str__(self):
        return f"Jornada de {self.assessor.username} em {self.data} - {self.km_total}km"

@receiver(m2m_changed, sender=CustomUser.groups.through)
def update_user_roles(sender, instance, action, **kwargs):
    """
    Sincroniza o campo 'is_assessor' do CustomUser com base nos seus grupos de permissões.
    Se o usuário estiver nos grupos 'Assessores' ou 'Consultores', is_assessor = True.
    """
    if action in ["post_add", "post_remove", "post_clear"]:
        is_assessor = instance.groups.filter(name__in=["Assessores", "Consultores"]).exists()
        if instance.is_assessor != is_assessor:
            CustomUser.objects.filter(pk=instance.pk).update(is_assessor=is_assessor)

class Configuracao(models.Model):
    valor_km_reembolso = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00, 
        verbose_name="Valor de Reembolso por KM"
    )
    grupos_podem_alterar_responsavel = models.ManyToManyField(
        'auth.Group',
        blank=True,
        verbose_name="Grupos que podem alterar o Responsável da visita",
        related_name='configuracoes_responsavel'
    )
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuração"
        verbose_name_plural = "Configurações"

    def __str__(self):
        return "Configurações Globais"

    @classmethod
    def get_solo(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj
