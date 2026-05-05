from datetime import date

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q
from django.utils import timezone

from .models import Visita, PerguntaRelatorio, RespostaRelatorio, Funcionario, VisitaFoto, Empresa
from .api_serializers import (
    VisitaAgendaSerializer,
    VisitaDetalheSerializer,
    PerguntaRelatorioSerializer,
    CheckinSerializer,
    CheckoutSerializer,
    RelatorioPayloadSerializer,
    UserSerializer,
    BugReportSerializer,
    FuncionarioSerializer,
    EmpresaSerializer,
    JornadaSerializer,
)
import json


def _is_admin(user):
    return user.is_superuser or getattr(user, 'is_admin', False)


def _empresas_visiveis_para_usuario(user):
    if _is_admin(user):
        return Empresa.objects.all()
    return Empresa.objects.filter(Q(assessor=user) | Q(assessores_autorizados=user)).distinct()


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def agenda_hoje(request):
    """
    Retorna as visitas de uma data para o assessor autenticado.
    GET /api/visitas/agenda/?data=YYYY-MM-DD
    """
    data_str = request.query_params.get('data')
    if data_str:
        try:
            target_date = date.fromisoformat(data_str)
        except ValueError:
            target_date = date.today()
    else:
        target_date = date.today()

    visitas = Visita.objects.filter(assessor=request.user, data=target_date).select_related('empresa')
    serializer = VisitaAgendaSerializer(visitas, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def agenda_mes(request):
    """
    Retorna as visitas de um mÃªs especÃ­fico para o assessor autenticado.
    GET /api/visitas/mes/?ano=YYYY&mes=MM
    """
    ano_str = request.query_params.get('ano')
    mes_str = request.query_params.get('mes')
    hoje = date.today()
    
    try:
        ano = int(ano_str) if ano_str else hoje.year
        mes = int(mes_str) if mes_str else hoje.month
    except ValueError:
        ano, mes = hoje.year, hoje.month

    visitas = Visita.objects.filter(
        assessor=request.user,
        data__year=ano, 
        data__month=mes
    ).select_related('empresa')
    
    serializer = VisitaAgendaSerializer(visitas, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def detalhe_visita(request, visita_id):
    """
    Retorna o detalhe de uma visita especÃ­fica pelo ID.
    GET /api/visitas/<id>/
    """
    try:
        visita = Visita.objects.get(id=visita_id, assessor=request.user)
    except Visita.DoesNotExist:
        return Response({'error': 'Visita nÃ£o encontrada.'}, status=status.HTTP_404_NOT_FOUND)
    serializer = VisitaDetalheSerializer(visita)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def calendario_visitas(request):
    """
    Retorna uma lista de datas futuras e passadas que contÃªm visitas.
    GET /api/visitas/calendario/
    """
    datas = Visita.objects.filter(assessor=request.user).values_list('data', flat=True).distinct()
    return Response([d.isoformat() for d in datas])

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def funcionarios_empresa(request, visita_id):
    """
    Retorna os funcionÃ¡rios da empresa atrelada Ã  visita.
    GET /api/visitas/<id>/funcionarios/
    """
    try:
        visita = Visita.objects.get(pk=visita_id, assessor=request.user)
    except Visita.DoesNotExist:
        return Response({'error': 'Visita nÃ£o encontrada.'}, status=status.HTTP_404_NOT_FOUND)
    
    funcionarios = Funcionario.objects.filter(empresa=visita.empresa)
    serializer = FuncionarioSerializer(funcionarios, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def perguntas_ativas(request):
    """
    Retorna todas as perguntas de relatÃ³rio ativas.
    GET /api/perguntas/
    """
    perguntas = PerguntaRelatorio.objects.filter(ativa=True)
    serializer = PerguntaRelatorioSerializer(perguntas, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def fazer_checkin(request, visita_id):
    """
    Registra o check-in de uma visita com GPS.
    POST /api/visitas/<id>/checkin/
    """
    try:
        visita = Visita.objects.get(pk=visita_id, assessor=request.user)
    except Visita.DoesNotExist:
        return Response({'error': 'Visita nÃ£o encontrada.'}, status=status.HTTP_404_NOT_FOUND)

    serializer = CheckinSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data
    visita.checkin_time = data['checkin_time']
    visita.checkin_lat = data['checkin_lat']
    visita.checkin_lng = data['checkin_lng']
    if data.get('justificativa_distancia'):
        visita.justificativa_distancia = data['justificativa_distancia']
    if request.data.get('is_offline_sync'):
        visita.sync_offline_flag = True
    visita.save(update_fields=['checkin_time', 'checkin_lat', 'checkin_lng', 'justificativa_distancia', 'sync_offline_flag'])
    return Response({'status': 'check-in realizado'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def fazer_checkout(request, visita_id):
    """
    Registra o check-out de uma visita com GPS.
    POST /api/visitas/<id>/checkout/
    """
    try:
        visita = Visita.objects.get(pk=visita_id, assessor=request.user)
    except Visita.DoesNotExist:
        return Response({'error': 'Visita nÃ£o encontrada.'}, status=status.HTTP_404_NOT_FOUND)

    serializer = CheckoutSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data
    visita.checkout_time = data['checkout_time']
    visita.checkout_lat = data['checkout_lat']
    visita.checkout_lng = data['checkout_lng']
    visita.status = 'realizada'
    if request.data.get('is_offline_sync'):
        visita.sync_offline_flag = True
    visita.save(update_fields=['checkout_time', 'checkout_lat', 'checkout_lng', 'status', 'sync_offline_flag'])
    return Response({'status': 'check-out realizado'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def enviar_relatorio(request, visita_id):
    """
    Recebe as respostas do relatÃ³rio, assinatura, contatoes e mÃºltiplas fotos via FormData.
    POST /api/visitas/<id>/responder/
    """
    try:
        visita = Visita.objects.get(pk=visita_id, assessor=request.user)
    except Visita.DoesNotExist:
        return Response({'error': 'Visita nÃ£o encontrada.'}, status=status.HTTP_404_NOT_FOUND)

    # Verifica se os dados vieram como JSON puro ou como FormData com JSON em string 'payload'
    if 'payload' in request.data:
        try:
            payload = json.loads(request.data['payload'])
        except json.JSONDecodeError:
            return Response({'error': 'Payload JSON invÃ¡lido.'}, status=status.HTTP_400_BAD_REQUEST)
    else:
        payload = request.data

    serializer = RelatorioPayloadSerializer(data=payload)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data

    if payload.get('is_offline_sync'):
        visita.sync_offline_flag = True
        visita.save(update_fields=['sync_offline_flag'])

    # Assinatura
    if data.get('assinatura'):
        visita.assinatura = data['assinatura']
        visita.save(update_fields=['assinatura'])

    # Contatoes
    prof_ids = data.get('contatoes_atendidos')
    if prof_ids is not None:
        visita.contatoes_atendidos.set(prof_ids)

    # Respostas
    if 'respostas' in data:
        for resp in data['respostas']:
            RespostaRelatorio.objects.update_or_create(
                visita=visita,
                pergunta_id=resp['pergunta'].id,
                defaults={'resposta': resp['resposta']},
            )

    # Fotos (Arquivos)
    fotos = request.FILES.getlist('fotos')
    for f in fotos:
        VisitaFoto.objects.create(visita=visita, imagem=f)

    return Response({'status': 'relatÃ³rio salvo com sucesso'})


@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def meu_perfil(request):
    """
    Retorna e atualiza as informaÃ§Ãµes do usuÃ¡rio atual.
    GET /api/users/me/
    PATCH /api/users/me/
    """
    user = request.user
    if request.method == 'GET':
        serializer = UserSerializer(user)
        return Response(serializer.data)
    
    elif request.method == 'PATCH':
        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reportar_bug(request):
    """
    Recebe um relatÃ³rio de erro/bug do aplicativo mobile.
    POST /api/bugs/
    """
    serializer = BugReportSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(usuario=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def lista_empresas(request):
    """
    Retorna as empresas vinculadas ao assessor.
    GET /api/empresas/
    """
    user = request.user
    empresas = _empresas_visiveis_para_usuario(user)
    
    serializer = EmpresaSerializer(empresas, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def lista_funcionarios(request):
    """
    Retorna os funcionÃ¡rios das empresas vinculadas ao assessor.
    GET /api/funcionarios/
    """
    user = request.user
    if _is_admin(user):
        funcionarios = Funcionario.objects.all()
    else:
        funcionarios = Funcionario.objects.filter(
            Q(empresa__assessor=user) | Q(empresa__assessores_autorizados=user)
        ).distinct()
    
    serializer = FuncionarioSerializer(funcionarios, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def criar_agendamento(request):
    """
    Cria um novo agendamento no mobile.
    POST /api/visitas/novo/
    """
    user = request.user
    empresa_id = request.data.get('empresa_id')
    data_str = request.data.get('data')
    horario_str = request.data.get('horario')

    if not (_is_admin(user) or getattr(user, 'is_assessor', False) or user.has_perm('core.add_visita')):
        return Response({'error': 'VocÃª nÃ£o tem permissÃ£o para criar agendamentos.'}, status=status.HTTP_403_FORBIDDEN)

    if not empresa_id or not data_str or not horario_str:
        return Response({'error': 'empresa_id, data e horario sÃ£o obrigatÃ³rios.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        empresa = _empresas_visiveis_para_usuario(user).get(id=empresa_id)
    except Empresa.DoesNotExist:
        return Response({'error': 'Empresa nÃ£o encontrada ou sem acesso.'}, status=status.HTTP_404_NOT_FOUND)

    try:
        from datetime import datetime
        data_obj = datetime.strptime(data_str, '%Y-%m-%d').date()
        horario_obj = datetime.strptime(horario_str, '%H:%M').time()
    except ValueError:
        return Response({'error': 'Formato de data ou horÃ¡rio invÃ¡lido.'}, status=status.HTTP_400_BAD_REQUEST)

    if not _is_admin(user):
        hoje = timezone.now().date()
        meses_diff = (data_obj.year - hoje.year) * 12 + data_obj.month - hoje.month
        if meses_diff != 1:
            return Response(
                {'error': 'VocÃª sÃ³ pode agendar visitas exatamente para o prÃ³ximo mÃªs.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

    visita = Visita.objects.create(
        empresa=empresa,
        assessor=user,
        data=data_obj,
        horario=horario_obj,
        status='agendada'
    )

    return Response({'status': 'agendamento criado com sucesso', 'id': visita.id}, status=status.HTTP_201_CREATED)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def status_jornada(request):
    from .models import Jornada
    hoje = date.today()
    jornada = Jornada.objects.filter(assessor=request.user, data=hoje).last()
    if jornada:
        serializer = JornadaSerializer(jornada)
        return Response(serializer.data)
    return Response({'status': 'nao_iniciada'}, status=200)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def iniciar_jornada(request):
    from .models import Jornada
    hoje = date.today()
    
    # Verifica se jÃ¡ tem jornada hoje e se estÃ¡ em andamento
    jornada = Jornada.objects.filter(assessor=request.user, data=hoje).last()
    if jornada and jornada.status == 'em_andamento':
        serializer = JornadaSerializer(jornada)
        return Response(serializer.data)
    
    lat = request.data.get('lat')
    lng = request.data.get('lng')
    
    jornada = Jornada.objects.create(
        assessor=request.user,
        inicio_lat=lat,
        inicio_lng=lng
    )
    serializer = JornadaSerializer(jornada)
    return Response(serializer.data, status=201)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sincronizar_jornada(request):
    from .models import Jornada
    hoje = date.today()
    jornada = Jornada.objects.filter(assessor=request.user, data=hoje, status='em_andamento').last()
    
    if not jornada:
        return Response({'error': 'Nenhuma jornada em andamento encontrada.'}, status=404)
        
    km_atual = request.data.get('km_total', 0.0)
    
    # Apenas atualiza se for maior para nÃ£o retroceder
    if float(km_atual) > jornada.km_total:
        jornada.km_total = float(km_atual)
        jornada.save(update_fields=['km_total'])
        
    serializer = JornadaSerializer(jornada)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def finalizar_jornada(request):
    from .models import Jornada
    from django.utils import timezone
    hoje = date.today()
    jornada = Jornada.objects.filter(assessor=request.user, data=hoje, status='em_andamento').last()
    
    if not jornada:
        return Response({'error': 'Nenhuma jornada em andamento encontrada.'}, status=404)
        
    lat = request.data.get('lat')
    lng = request.data.get('lng')
    km_total = request.data.get('km_total')
    
    jornada.fim_time = timezone.now()
    jornada.fim_lat = lat
    jornada.fim_lng = lng
    jornada.status = 'finalizada'
    
    if km_total is not None and float(km_total) > jornada.km_total:
        jornada.km_total = float(km_total)
        
    jornada.save(update_fields=['fim_time', 'fim_lat', 'fim_lng', 'status', 'km_total'])
    
    serializer = JornadaSerializer(jornada)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def criar_empresa(request):
    """
    Cria uma nova empresa via mobile.
    POST /api/empresas/nova/
    """
    if not (_is_admin(request.user) or request.user.has_perm('core.add_empresa')):
        return Response({'error': 'Você não tem permissão para cadastrar empresas.'}, status=status.HTTP_403_FORBIDDEN)
        
    nome = request.data.get('nome')
    if not nome:
        return Response({'error': 'Nome da empresa Ã© obrigatÃ³rio.'}, status=status.HTTP_400_BAD_REQUEST)
        
    empresa = Empresa.objects.create(
        nome=nome,
        telefone=request.data.get('telefone', ''),
        email=request.data.get('email', ''),
        assessor=request.user,
        status='N'
    )
    
    # Adicionar o usuÃ¡rio tambÃ©m na lista de autorizados, caso a regra de negÃ³cio exija
    empresa.assessores_autorizados.add(request.user)
    
    return Response({'status': 'empresa criada com sucesso', 'id': empresa.id}, status=status.HTTP_201_CREATED)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def criar_funcionario(request):
    """
    Cria um novo funcionÃ¡rio via mobile.
    POST /api/funcionarios/novo/
    """
    if not (_is_admin(request.user) or request.user.has_perm('core.add_funcionario')):
        return Response({'error': 'Você não tem permissão para cadastrar funcionários.'}, status=status.HTTP_403_FORBIDDEN)
        
    nome = request.data.get('nome')
    empresa_id = request.data.get('empresa_id')
    
    if not nome or not empresa_id:
        return Response({'error': 'Nome e empresa_id sÃ£o obrigatÃ³rios.'}, status=status.HTTP_400_BAD_REQUEST)
        
    try:
        empresa = _empresas_visiveis_para_usuario(request.user).get(id=empresa_id)
    except Empresa.DoesNotExist:
        return Response({'error': 'Empresa nÃ£o encontrada.'}, status=status.HTTP_404_NOT_FOUND)
        
    funcionario = Funcionario.objects.create(
        nome=nome,
        empresa=empresa,
        telefone=request.data.get('telefone', ''),
        email=request.data.get('email', ''),
        departamento=request.data.get('departamento', ''),
        cargo=request.data.get('cargo', '')
    )
    
    return Response({'status': 'funcionÃ¡rio criado com sucesso', 'id': funcionario.id}, status=status.HTTP_201_CREATED)

