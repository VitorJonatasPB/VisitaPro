# 📱 Documentação Completa - Regras de Negócio App Mobile VisitaPro

**Versão:** 1.0  
**Data:** 5 de Maio de 2026  
**Aplicativo:** VisitaPro Mobile (React Native + Expo)

---

## 📑 Índice

1. [Visão Geral do Sistema](#1-visão-geral-do-sistema)
2. [Arquitetura](#2-arquitetura)
3. [Modelos de Dados](#3-modelos-de-dados)
4. [Fluxos de Negócio](#4-fluxos-de-negócio)
5. [Regras de Acesso e Permissões](#5-regras-de-acesso-e-permissões)
6. [Ciclo de Vida da Visita](#6-ciclo-de-vida-da-visita)
7. [Geolocalização e Geofencing](#7-geolocalização-e-geofencing)
8. [Jornada de Trabalho](#8-jornada-de-trabalho)
9. [Relatórios e Coleta de Dados](#9-relatórios-e-coleta-de-dados)
10. [Modo Offline e Sincronização](#10-modo-offline-e-sincronização)
11. [Validações e Restrições](#11-validações-e-restrições)
12. [Tratamento de Erros](#12-tratamento-de-erros)

---

## 1. Visão Geral do Sistema

### Propósito
O VisitaPro é um sistema de gerenciamento de visitas de consultores em empresas. O aplicativo mobile permite que consultores registrem sua presença em campo com:
- ✅ Validação de localização (geofencing)
- ✅ Coleta de dados via questionários dinâmicos
- ✅ Assinatura digital
- ✅ Fotos de evidência
- ✅ Operação offline com sincronização posterior

### Usuários Principais
1. **Assessores/Consultores**: Usuários que fazem as visitas (via app mobile)
2. **Administradores**: Gerenciam empresas, perguntas e relatórios (painel web)
3. **Superadministradores**: Controle total do sistema

---

## 2. Arquitetura

### Stack Tecnológico - Mobile

| Componente | Tecnologia | Versão |
|-----------|-----------|--------|
| Framework | React Native + Expo | 54.0 |
| Linguagem | TypeScript | - |
| Roteamento | Expo Router | 6.0 |
| Requisições HTTP | Axios / Fetch API | - |
| State Management | React Query (TanStack) | 5.99 |
| Armazenamento Local | AsyncStorage | 2.2 |
| Localização | Expo Location | 19.0 |
| Assinatura | react-native-signature-canvas | 5.0 |
| Autenticação | JWT (SimpleJWT Backend) | - |
| Cache de Imagens | Expo Image | 3.0 |
| Seletor de Documentos | Expo Document Picker | 14.0 |

### Arquitetura de Camadas

```
┌─────────────────────────────────────┐
│     UI (Screens + Components)       │
├─────────────────────────────────────┤
│     Services (API, Storage, Sync)   │
├─────────────────────────────────────┤
│   AsyncStorage (Cache Local)        │
├─────────────────────────────────────┤
│   Django REST API (Backend)         │
├─────────────────────────────────────┤
│   PostgreSQL / SQLite (BD)          │
└─────────────────────────────────────┘
```

---

## 3. Modelos de Dados

### 3.1 CustomUser (Usuário Autenticado)

**Responsabilidade**: Representar um consultor ou administrador no sistema.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | Integer | ID único |
| `username` | String | Nome de usuário (único) |
| `email` | Email | Email do usuário |
| `first_name` | String | Primeiro nome |
| `last_name` | String | Sobrenome |
| `is_assessor` | Boolean | Marca como consultor |
| `is_admin` | Boolean | Marca como administrador local |
| `is_active` | Boolean | Ativo ou desativado |
| `telefone` | String(20) | Telefone de contato |
| `foto` | ImageField | Foto de perfil |
| `cor_mapa` | String(7) | Cor do pin no mapa (hex: #RRGGBB) |

**Regra de Negócio**: 
- ✅ **Sistema de Controle de Acesso Baseado em Grupos**: Usuários são criados e então adicionados a grupos de permissão
- ✅ **Múltiplos Papéis**: Um usuário pode estar em múltiplos grupos (`assessor` E `admin` simultaneamente)
- ✅ **Herança de Permissões**: Campos `is_assessor` e `is_admin` refletem a pertencência ao grupo (não mutualmente exclusivos)
- ✅ **Superadministrador**: Super usuários (Django `is_superuser=True`) têm acesso irrestrito
- ✅ **Customização Visual**: A cor do mapa personaliza a exibição do pin do assessor no painel web

---

### 3.2 Empresa

**Responsabilidade**: Representar as empresas clientes que recebem visitas.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | Integer | ID único |
| `nome` | String(150) | Nome da empresa |
| `status` | Choice | 'A' (Ativa), 'I' (Inativa), 'N' (Em Negociação) |
| `assessor` | FK(CustomUser) | Assessor principal responsável |
| `assessores_autorizados` | M2M(CustomUser) | Outros assessores autorizados |
| `cnpj_cpf` | String(18) | CNPJ ou CPF |
| `telefone` | String(20) | Telefone |
| `email` | Email | Email |
| `cep` | String(10) | CEP (formato: 12345-678) |
| `rua` | String(255) | Via pública |
| `numero` | String(20) | Número |
| `bairro` | String(100) | Bairro |
| `cidade` | String(100) | Cidade |
| `estado` | String(2) | UF (ex: SP, RJ) |
| `latitude` | String(50) | Latitude (geocodificação) |
| `longitude` | String(50) | Longitude (geocodificação) |
| `data_conversao` | Date | Data de mudança N→A |
| `ultima_visita` | Date | Data da última visita |

**Regras de Negócio**:
- ✅ **Geocodificação Automática**: Ao salvar com CEP, preenchimento automático via ViaCEP
- ✅ **Geocodificação Google**: Se coordenadas vazias, tenta Google Maps API
- ✅ **Tracking de Conversão**: Quando status muda de 'N' (Negociação) para 'A' (Ativa), registra `data_conversao`
- ✅ **Visibilidade para Assessor**: Um assessor só vê empresas onde é responsável OU está autorizado
- ✅ **Acesso Admin**: Admins veem todas as empresas

---

### 3.3 Visita

**Responsabilidade**: Representar uma visita agendada ou realizada a uma empresa.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | Integer | ID único |
| `empresa` | FK(Empresa) | Empresa visitada |
| `assessor` | FK(CustomUser) | Assessor que faz a visita |
| `data` | Date | Data da visita agendada |
| `horario` | Time | Horário agendado |
| `status` | Choice | 'agendada', 'realizada', 'cancelada' |
| `observacoes` | Text | Observações gerais |
| `relatorio` | Text | Relatório preenchido |
| `nome_responsavel` | String(200) | Nome quem assinou |
| `assinatura` | Text | Assinatura (Base64) |
| `contatoes_atendidos` | M2M(Funcionario) | Funcionários participantes |
| `checkin_time` | DateTime | Data/hora do check-in |
| `checkin_lat` | String(50) | Latitude do check-in |
| `checkin_lng` | String(50) | Longitude do check-in |
| `checkout_time` | DateTime | Data/hora do check-out |
| `checkout_lat` | String(50) | Latitude do check-out |
| `checkout_lng` | String(50) | Longitude do check-out |
| `justificativa_distancia` | Text | Justificativa se fora do raio |
| `sync_offline_flag` | Boolean | Sincronizado via cache offline |
| `criado_em` | DateTime | Data de criação |
| `atualizado_em` | DateTime | Data da última atualização |

**Regras de Negócio**:
- ✅ **Ciclo de Vida**: `agendada` → `realizada` (após check-out) ou `cancelada`
- ✅ **Ownership**: Apenas o assessor que agendou pode editar
- ✅ **Check-in Obrigatório**: Antes de responder perguntas
- ✅ **Geofencing Obrigatório**: Check-in deve validar localização
- ❌ **Assinatura Obrigatória**: (Removido) Não é mais obrigatória para finalizar a visita
- ✅ **Ordering**: Ordenadas por data DESC, horário DESC

---

### 3.4 Funcionário

**Responsabilidade**: Representar colaboradores da empresa (contatos).

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | Integer | ID único |
| `nome` | String(150) | Nome completo |
| `matricula` | String(50) | Matrícula (opcional) |
| `empresa` | FK(Empresa) | Empresa vinculada |
| `departamento` | String(100) | Departamento |
| `cargo` | String(100) | Cargo/Função |
| `telefone` | String(20) | Telefone |
| `email` | Email | Email corporativo |
| `criado_em` | DateTime | Data de criação |
| `atualizado_em` | DateTime | Data da última atualização |

**Regras de Negócio**:
- ✅ Um funcionário pertence a uma empresa
- ✅ Consultores selecionam funcionários atendidos durante a visita
- ✅ Nome de tabela no BD: `core_funcionario` (Padronizado)

---

### 3.5 PerguntaRelatorio

**Responsabilidade**: Perguntas dinâmicas que consultores respondem durante visitas.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | Integer | ID único |
| `texto` | String(255) | Enunciado da pergunta |
| `tipo_resposta` | Choice | Tipo de campo (vide abaixo) |
| `opcoes_resposta` | String(500) | Opções (para múltipla escolha) |
| `fonte_dados` | String(50) | Origem dos dados (ex: 'funcionarios') |
| `ativa` | Boolean | Pergunta ativa/desativa |
| `criado_em` | DateTime | Data de criação |

**Tipos de Pergunta Suportados**:

| Tipo | Descrição | Exemplo |
|------|-----------|---------|
| `texto` | Texto curto (até 255 car) | "Qual é o nome da empresa?" |
| `texto_longo` | Texto sem limite | "Descreva as condições da empresa" |
| `data` | Seletor de data (calendário) | "Data da última inspeção?" |
| `booleano` | Sim/Não | "Documentação em dia?" |
| `numero` | Campo numérico | "Quantidade de funcionários?" |
| `multipla_escolha` | Opções com múltiplas respostas | "Quais serviços?; Opção1,Opção2" |
| `lista_suspensa` | Dropdown (manual ou dinâmico) | Pode ser estático ou vindo de `fonte_dados` |

**Regras de Negócio**:
- ✅ Apenas perguntas ativas (`ativa=True`) aparecem no app
- ✅ Para `lista_suspensa`, se `fonte_dados` está preenchido, carrega dados dinamicamente
- ✅ Perguntas podem ser modificadas, mas respostas antigas não são afetadas
- ✅ Sem duplicação: tipo e texto únicos por criação

---

### 3.6 RespostaRelatorio

**Responsabilidade**: Armazenar as respostas dos consultores para cada pergunta em uma visita.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | Integer | ID único |
| `visita` | FK(Visita) | Visita relacionada |
| `pergunta` | FK(PerguntaRelatorio) | Pergunta respondida |
| `resposta` | Text | Valor da resposta (formato livre) |
| `unique_together` | - | (visita, pergunta) - uma resposta por pergunta |

**Regras de Negócio**:
- ✅ Uma pergunta por visita (chave única `visita + pergunta`)
- ✅ Respostas são sempre texto (conversão no client)
- ✅ Histórico preservado: cada edição cria nova resposta
- ✅ Update-or-create pattern: garante apenas uma resposta

---

### 3.7 VisitaFoto

**Responsabilidade**: Armazenar fotos/evidências da visita.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | Integer | ID único |
| `visita` | FK(Visita) | Visita relacionada |
| `imagem` | ImageField | Arquivo de imagem |
| `data_upload` | DateTime | Quando foi feito upload |

**Regras de Negócio**:
- ✅ Múltiplas fotos por visita (relação 1-N)
- ✅ Armazenadas em `media/visitas_fotos/`
- ✅ Timestamp automático de upload

---

### 3.8 Jornada

**Responsabilidade**: Rastrear a jornada de trabalho diária de um assessor (trajetos, quilometragem).

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | Integer | ID único |
| `assessor` | FK(CustomUser) | Assessor responsável |
| `data` | Date | Data da jornada |
| `inicio_time` | DateTime | Horário início |
| `inicio_lat` | String(50) | Latitude inicial |
| `inicio_lng` | String(50) | Longitude inicial |
| `fim_time` | DateTime | Horário fim |
| `fim_lat` | String(50) | Latitude final |
| `fim_lng` | String(50) | Longitude final |
| `km_total` | Float | Quilometragem total |
| `status` | Choice | 'em_andamento' ou 'finalizada' |

**Regras de Negócio**:
- ✅ Uma jornada por assessor por dia
- ✅ Status muda: `em_andamento` → `finalizada`
- ✅ KM sincroniza incrementalmente a cada 5 minutos
- ✅ Rastreamento GPS com distância mínima de 5m e máxima de 10km por tick

---

### 3.9 BugReport

**Responsabilidade**: Permitir consultores reportarem erros no app.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | Integer | ID único |
| `usuario` | FK(CustomUser) | Usuário que reportou |
| `descricao` | Text | Descrição do erro |
| `device_info` | String(255) | Info do dispositivo (SO, modelo) |
| `resolvido` | Boolean | Flag de resolução |
| `criado_em` | DateTime | Data do report |

**Regras de Negócio**:
- ✅ Qualquer assessor autenticado pode reportar
- ✅ Aparece em dashboard do admin para triagem
- ✅ Ordenado por data DESC (mais recente primeiro)

---

### 3.10 LogAlteracao

**Responsabilidade**: Auditoria de mudanças em visitas.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | Integer | ID único |
| `visita` | FK(Visita) | Visita modificada |
| `usuario` | FK(CustomUser) | Usuário que fez a mudança |
| `data` | DateTime | Quando a mudança ocorreu |
| `descricao` | Text | O que foi alterado |

**Regras de Negócio**:
- ✅ Criado automaticamente ao salvar mudanças em visitas
- ✅ Imutável (não permite edição)

---

## 4. Fluxos de Negócio

### 4.1 Fluxo de Login

```
┌─────────────────┐
│   Tela Login    │
└────────┬────────┘
         │ Envia credenciais
         ▼
┌─────────────────────────────┐
│ POST /api/token/            │
│ {username, password}        │
└────────┬────────────────────┘
         │
    ┌────▼─────┐
    │ Válido?   │
    └─┬──────┬──┘
      │ ✓    │ ✗
      │      └─────→ Alert "Credenciais Inválidas"
      ▼
┌──────────────────────────┐
│ Salvar tokens em Storage │
│ - access_token           │
│ - refresh_token          │
└──────────┬───────────────┘
           │
           ▼
┌──────────────────┐
│ Dashboard Mobile │
│ (Agenda/Home)    │
└──────────────────┘
```

**Detalhes**:
- ✅ Backend usa **SimpleJWT** (Django REST Framework)
- ✅ Tokens salvos em **AsyncStorage** com prefixo `@visitaspro:access_token` e `@visitaspro:refresh_token`
- ✅ Token incluso em header: `Authorization: Bearer {token}`
- ✅ Timeout de 10 segundos para requisições
- ✅ Se token expirado (401), limpa e redireciona para login

---

### 4.2 Fluxo de Sincronização de Dados

```
┌──────────────────────────┐
│   App Abre / Refresh     │
└──────────────┬───────────┘
              │
         ┌────▼──────┐
         │ Online?   │
         └─┬───────┬─┘
           │ ✓     │ ✗
           │       └─→ Usa dados locais (AsyncStorage)
           ▼
    ┌──────────────────────────────┐
    │ Sincroniza Dados do Servidor │
    │ - GET /api/visitas/agenda/   │
    │ - GET /api/perguntas/        │
    │ - GET /api/empresas/         │
    └──────────┬───────────────────┘
               │
    ┌──────────▼────────────────┐
    │ Salva em AsyncStorage:     │
    │ @cache_/api/visitas/...    │
    │ @cache_/api/perguntas/...  │
    └──────────┬────────────────┘
               │
               ▼
    ┌──────────────────┐
    │ Atualiza UI      │
    │ com dados frescos │
    └──────────────────┘
```

**Detalhes**:
- ✅ Sincronização automática ao abrir o app
- ✅ Pull-to-refresh na agenda
- ✅ Cache em `AsyncStorage` com chaves `@cache_{endpoint}`
- ✅ Fallback para cache se servidor indisponível

---

### 4.3 Fluxo de Processamento da Fila Offline

```
┌──────────────────────────┐
│ User Faz Check-in/Report │
│ (Sem Internet)           │
└──────────────┬───────────┘
              │
    ┌─────────▼──────────┐
    │ addToQueue()        │
    │ - Gera ID único     │
    │ - Salva em Storage  │
    │ @api_queue          │
    └─────────┬───────────┘
              │
    ┌─────────▼──────────────┐
    │ Alert: "Modo Offline"  │
    │ "Enviado quando online"│
    └─────────┬──────────────┘
              │
    ┌─────────▼──────────┐
    │ Internet Volta?    │
    │ (Background/Sync)  │
    └────┬────────────┬──┘
         │ ✓          │ ✗
         │            └─→ Fila persiste
         ▼
    ┌──────────────────────┐
    │ processQueue()       │
    │ - Pega fila          │
    │ - Retry 3x por item  │
    │ - Remove se sucesso  │
    │ - Update tentativas  │
    └──────────┬───────────┘
              │
         ┌────▼────┐
         │ Sucesso?│
         └────┬────┘
         ✓    │    ✗
             └────→ Tenta novamente depois
```

**Detalhes**:
- ✅ Items fila: `{id, endpoint, method, payload, timestamp, type}`
- ✅ Tipos: `CHECKIN`, `CHECKOUT`, `RELATORIO`, `BUG`
- ✅ Max 3 tentativas por item
- ✅ Processamento quando reconecta
- ✅ Sincronização a cada 5 minutos (background)

---

## 5. Regras de Acesso e Permissões

### 5.1 Matriz de Permissões

| Recurso | Assessor Puro | Admin Puro | Admin + Assessor | Super | Anônimo |
|---------|---------------|-----------|------------------|-------|---------|
| Ver agenda própria | ✅ | ❌ | ✅ | ✅ | ❌ |
| Ver empresas autorizadas | ✅ | ✅ | ✅ | ✅ | ❌ |
| Editar empresas próprias | ❌ | ✅ | ✅ | ✅ | ❌ |
| Criar visitas agendadas | ❌ | ✅ | ✅ | ✅ | ❌ |
| Fazer check-in/out (próprias) | ✅ | ❌ | ✅ | ✅ | ❌ |
| Responder perguntas | ✅ | ❌ | ✅ | ✅ | ❌ |
| Ver relatórios | ❌ | ✅ | ✅ | ✅ | ❌ |
| Gerenciar usuários | ❌ | ❌ | ❌ | ✅ | ❌ |
| Reportar bugs | ✅ | ✅ | ✅ | ✅ | ❌ |

**Notas**:
- ✅ Um usuário pode estar em múltiplos grupos (Ex: `is_assessor=True` E `is_admin=True` simultaneamente)
- ✅ Quando um usuário está em múltiplos grupos, herda permissões de TODOS os grupos
- ✅ Super usuários contornam todas as validações de permissão

### 5.1.1 Sistema de Controle de Acesso Baseado em Grupos

**Fluxo de Criação de Usuário**:

```
┌──────────────────┐
│ Usuário Criado   │
│ (is_active=True) │
└────────┬─────────┘
         │
    ┌────▼───────────────────────────┐
    │ Admin Adiciona a Grupos:        │
    │ - Grupo "Assessores"           │
    │   └─ Set is_assessor=True      │
    │ - Grupo "Administradores"      │
    │   └─ Set is_admin=True         │
    │ - Grupo "Supervisores" (opcional)
    └────┬───────────────────────────┘
         │
    ┌────▼─────────────────────────┐
    │ Usuário Recebe Permissões:   │
    │ - Herança do grupo 1         │
    │ - Herança do grupo 2         │
    │ - Herança combinada          │
    └──────────────────────────────┘
```

**Grupos Disponíveis**:

| Grupo | Flag | Permissões |
|-------|------|-----------|
| Assessores | `is_assessor=True` | Ver agenda, fazer check-in/out, responder perguntas, reportar bugs |
| Administradores | `is_admin=True` | Gerenciar empresas, criar visitas, ver relatórios, gerenciar perguntas |
| Supervisores | Ambos `True` | Todas as permissões (assessor + admin) + revisão de dados |
| Superadministrador | `is_superuser=True` | Acesso irrestrito + gerenciamento de usuários |

**Validação de Acesso por Endpoint**:

```python
# Assessor pode fazer check-in de suas visitas
if user.is_assessor:
    visitas = Visita.objects.filter(assessor=user)

# Admin pode gerenciar empresas
if user.is_admin:
    empresas = Empresa.objects.all()  # Ou filtrado

# Combinação: supervisor (assessor + admin)
if user.is_assessor and user.is_admin:
    # Pode tanto fazer visitas quanto gerenciar empresas
    pass

# Super: ignora todas as restrições
if user.is_superuser:
    # Acesso a TUDO
    pass
```

### 5.3 Modelo de Autorização por Endpoint

**Padrão REST Framework**:
```python
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def endpoint(request):
    # Usa token JWT do header Authorization
    # Verifica `is_authenticated` automaticamente
```

**Validação de Ownership**:
```python
# Apenas o assessor da visita pode editar
visita = Visita.objects.get(pk=id, assessor=request.user)

# Admin pode editar qualquer empresa
if not (user.is_superuser or user.is_admin):
    raise PermissionDenied()

# Admin + Assessor pode fazer ambos
if user.is_admin:  # tem permissão admin
    empresas = Empresa.objects.all()
if user.is_assessor:  # também tem permissão assessor
    visitas = Visita.objects.filter(assessor=user)
```

**Visibilidade de Empresas**:
```python
def _empresas_visiveis_para_usuario(user):
    # Se for admin: vê TODAS as empresas
    if user.is_superuser or user.is_admin:
        return Empresa.objects.all()
    
    # Se for assessor: vê apenas suas empresas
    if user.is_assessor:
        return Empresa.objects.filter(
            Q(assessor=user) | Q(assessores_autorizados=user)
        )
    
    # Nenhuma permissão: lista vazia
    return Empresa.objects.none()
```

### 5.4 Refresh de Token

**Quando**: Access token próximo de expirar

**Fluxo**:
```
Token enviado no header
      ↓
Backend valida (JWT)
      ↓
  ┌───▼─────┐
  │ Válido? │
  └───┬──┬──┘
    ✓ │  │ ✗ (Expirado)
      │  └──────→ POST /api/token/refresh/
      │          {refresh_token}
      │          ↓
      │    ┌─────▼─────┐
      │    │ Novo token?│
      │    └─────┬─────┘
      │      ✓   │   ✗
      └──────┴───┴──→ Redireciona para login
```

---

## 6. Ciclo de Vida da Visita

### 6.1 Estados da Visita

```
    ┌─────────────┐
    │ AGENDADA    │
    │ (Inicial)   │
    └────┬────────┘
         │
    ┌────▼───────────────────────┐
    │ Assessor faz Check-in?      │
    └────┬──────────────────┬─────┘
         │ ✓                │ ✗
         │                  └─→ CANCELADA (Admin cancela)
         │
    ┌────▼──────────────────────────┐
    │ Responde Perguntas +          │
    │ Assinatura + Fotos?           │
    └────┬──────────────┬───────────┘
         │ ✓            │ ✗
         │              └─→ Fica em aberto (pode completar depois)
         │
    ┌────▼─────────────────────┐
    │ Faz Check-out?           │
    │ (GPS + Timestamp)        │
    └────┬────────┬────────────┘
         │ ✓      │ ✗
         │        └─→ Fica em aberto (pode fazer depois)
         │
    ┌────▼──────────────────────┐
    │ Status muda para REALIZADA│
    └───────────────────────────┘
```

**Importante**: 
- ✅ Não há transição direta de AGENDADA para CANCELADA (só via admin)
- ✅ Uma visita pode ficar com check-in e checkout incompleto
- ✅ Não há penalidade por responder perguntas depois
- ✅ Assinatura é OBRIGATÓRIA para finalizar

### 6.2 Validações por Estado

| Estado | Ações Permitidas | Validações |
|--------|-----------------|-----------|
| `agendada` | Check-in | Geofencing, GPS obrigatório |
| `realizada` (mid-flow) | Responder, Assinar, Fotos, Funcionários | Nenhuma |
| `realizada` (completa) | Ver histórico | Nenhuma |
| `cancelada` | Apenas leitura | Nenhuma |

### 6.3 Timestamps e Ordenação

- **Ordenação padrão**: Data DESC, Horário DESC (visitas mais recentes primeiro)
- **Filtros comuns**:
  - Por data: `GET /api/visitas/agenda/?data=YYYY-MM-DD`
  - Por mês: `GET /api/visitas/mes/?ano=YYYY&mes=MM`
  - Calendário: `GET /api/visitas/calendario/` (retorna datas com visitas)

---

## 7. Geolocalização e Geofencing

### 7.1 Configuração de Raio de Geofencing

**Raio Padrão**: **500 metros**

**Localização no código**:
- Mobile: `mobile/app/visita/[id].tsx` linha ~146
- Backend: Implementado no mobile (validação no checkin)

```typescript
// Cálculo de distância (Fórmula de Haversine)
const haversineDistancia = (lat1, lng1, lat2, lng2): number => {
  const R = 6371000; // raio da Terra em metros
  const toRad = (v) => (v * Math.PI) / 180;
  const dLat = toRad(lat2 - lat1);
  const dLng = toRad(lng2 - lng1);
  const a = Math.sin(dLat / 2) ** 2 +
            Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * 
            Math.sin(dLng / 2) ** 2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
};

// Validação no Check-in
if (dist > 500) {
  // Abre modal pedindo justificativa
  setShowGeofenceModal(true);
}
```

### 7.2 Fluxo de Check-in com Geofencing

```
User clica "Check-in"
      │
      ▼
┌──────────────────────┐
│ Solicita permissão   │
│ de localização       │
└────────┬─────────────┘
         │
    ┌────▼──────┐
    │ Granted?  │
    └────┬───┬──┘
         │✓  │✗
         │   └─→ Alert "Permissão negada"
         │
    ┌────▼────────────────────┐
    │ Obtém GPS atual com     │
    │ alta precisão          │
    └────┬────────────────────┘
         │
    ┌────▼─────────────────────────────┐
    │ Calcula distância até empresa:   │
    │ dist = haversine(GPS, Empresa)  │
    └────┬──────────────┬──────────────┘
         │ dist <= 500m │ dist > 500m
         │              │
    ┌────▼──────────┐  ┌────▼─────────────────┐
    │ Check-in OK   │  │ Modal: Justificativa │
    │ POST /checkin/│  │ "Você está a X m"    │
    └──────────────┘  │ Input: texto         │
                      │ "Por que fora raio?" │
                      └────┬─────────────────┘
                           │
                      ┌────▼───────┐
                      │ Submit?     │
                      └────┬───┬───┘
                           │✓  │✗
                           │   └─→ Cancela
                           │
                    ┌──────▼────────────┐
                    │ POST /checkin/    │
                    │ + justificativa   │
                    └───────────────────┘
```

**Payload de Check-in**:
```json
{
  "checkin_lat": "-23.550520",
  "checkin_lng": "-46.633308",
  "checkin_time": "2026-05-05T14:30:00Z",
  "justificativa_distancia": "Estacionamento longe"  // opcional
}
```

### 7.3 Rastreamento de Jornada (Waypoints)

**Precisão**: 
- Update apenas se mover > 50 metros (economia de bateria)
- Intervalo de 30 segundos mínimo
- Intervalo de sincronização: 5 minutos

**Cálculo de Distância com Filtros**:
```typescript
// Ignora "pulos" de GPS absurdos
if (distancia > 5 && distancia < 10000) {
  km_total += distancia / 1000; // converte para km
}
```

**Limite de Waypoints**: 200 máximos em memória (evita estouro)

---

## 8. Jornada de Trabalho

### 8.1 Ciclo de Vida da Jornada

```
┌─────────────┐
│ NÃO INICIADA│
└──────┬──────┘
       │ User clica "Iniciar Jornada"
       ▼
┌──────────────────────────┐
│ EM ANDAMENTO             │
│ - Inicia rastreamento GPS│
│ - Registra data/hora/loc │
└──────┬────────────────────┘
       │ (User trabalha o dia todo)
       │ GPS monitora a cada 30s
       │ KM sincroniza a cada 5min
       │
       ▼ User clica "Finalizar Jornada"
┌──────────────────────────┐
│ FINALIZADA               │
│ - Para rastreamento      │
│ - Registra fim_time/loc  │
│ - Sincroniza KM final    │
└──────────────────────────┘
```

### 8.2 Endpoints de Jornada

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/api/jornada/status/` | GET | Estado atual da jornada |
| `/api/jornada/iniciar/` | POST | Inicia nova jornada |
| `/api/jornada/sincronizar/` | POST | Sincroniza KM do dia |
| `/api/jornada/finalizar/` | POST | Finaliza jornada |

**Exemplo - Iniciar Jornada**:
```json
POST /api/jornada/iniciar/
{
  "inicio_lat": "-23.550520",
  "inicio_lng": "-46.633308"
}
```

**Exemplo - Sincronizar KM**:
```json
POST /api/jornada/sincronizar/
{
  "km_total": 45.7
}
```

**Validação de KM**: 
- ✅ Só atualiza se `km_atual > jornada.km_total` (sempre crescente)
- ✅ Sincronização periódica a cada 5 minutos
- ✅ Quando conexão volta, envia KM máximo até então

### 8.3 Armazenamento Local de Jornada

**Storage Keys**:
```
@visitaspro:jornada_estado  → { status, km_total, last_lat, last_lng }
@visitaspro:jornada_waypoints → Array de { lat, lng }
```

**Estado Local**:
```typescript
interface JornadaState {
  status: 'nao_iniciada' | 'em_andamento' | 'pausada' | 'finalizada';
  km_total: number;
  last_lat?: number;
  last_lng?: number;
}
```

---

## 9. Relatórios e Coleta de Dados

### 9.1 Ciclo de Preenchimento do Relatório

```
┌──────────────────┐
│ Check-in Feito?  │
└────┬──────┬──────┘
     │✓     │✗
     │      └─→ Alert "Faça check-in primeiro"
     │
     ▼
┌─────────────────────────────────┐
│ Carrega Perguntas Ativas       │
│ GET /api/perguntas/             │
│ (Já em cache offline)           │
└────────┬────────────────────────┘
         │
    ┌────▼──────────────────┐
    │ User Responde Cada:   │
    │ - Campo de texto      │
    │ - Campo numérico      │
    │ - Selector (dropdown) │
    │ - Múltipla escolha    │
    │ - Calendário (data)   │
    │ - Sim/Não             │
    └────┬──────────────────┘
         │
    ┌────▼──────────────────────┐
    │ Seleciona Funcionários     │
    │ Atendidos                  │
    └────┬──────────────────────┘
         │
    ┌────▼──────────────────────┐
    │ Captura Assinatura        │
    │ (Tela horizontal)         │
    └────┬──────────────────────┘
         │
    ┌────▼──────────────────────┐
    │ Fotografa Evidências      │
    │ (Câmera ou Galeria)       │
    └────┬──────────────────────┘
         │
    ┌────▼──────────────────────┐
    │ Faz Check-out             │
    │ POST /api/visitas/{id}/    │
    │ checkout/                  │
    └────┬──────────────────────┘
         │
    ┌────▼──────────────────────────┐
    │ Envia Relatório              │
    │ POST /api/visitas/{id}/      │
    │ responder/                    │
    │ (FormData com payload JSON)   │
    └──────────────────────────────┘
```

### 9.2 Estrutura do Payload de Relatório

```typescript
POST /api/visitas/{id}/responder/

FormData {
  payload: JSON.stringify({
    respostas: [
      { pergunta: 1, resposta: "Sim" },
      { pergunta: 2, resposta: "50 pessoas" },
      { pergunta: 3, resposta: "2026-05-10" }
    ],
    assinatura: "data:image/png;base64,...", // Base64 da assinatura
    contatoes_atendidos: [1, 5, 12], // IDs dos funcionários
    is_offline_sync: false  // Flag se sincronizado offline
  }),
  fotos: [File, File, ...] // Array de arquivos de imagem
}
```

### 9.3 Validações no Relatório

- ❌ **Assinatura Obrigatória**: (Removido) O envio agora é permitido sem assinatura
- ✅ **Mínimo 1 Pergunta**: Deve responder pelo menos uma
- ✅ **Check-in Anterior**: Deve fazer check-in antes de responder
- ✅ **Update-or-Create**: Se pergunta já respondida, atualiza (não duplica)
- ✅ **Fotos Opcionais**: Pode ter 0 ou mais fotos

### 9.4 Tipos de Questões e Validações

| Tipo | Validação | Exemplo |
|------|-----------|---------|
| `texto` | Max 255 chars | ✅ "A empresa estava limpa" |
| `texto_longo` | Sem limite | ✅ "Descrição detalhada..." |
| `data` | Formato YYYY-MM-DD | ✅ "2026-05-05" |
| `numero` | Parse como float | ✅ "123.45" |
| `booleano` | "true" ou "false" | ✅ "true" |
| `multipla_escolha` | Lista de valores | ✅ "Op1,Op2,Op3" |
| `lista_suspensa` | Um valor | ✅ "Opção Selecionada" |

### 9.5 Geração de Relatórios (Backend)

**Tipos de Relatório Disponíveis**:

1. **Resumo Geral** (`resumo_geral`)
   - Total de visitas (agendadas, realizadas, canceladas)
   - Status de empresas (ativas, inativas, em negociação)
   - Taxa de conversão
   - Média de visitas por empresa
   - Distância média percorrida

2. **Performance de Assessor** (`performance_assessor`)
   - Visitas por assessor
   - Taxa de cumprimento
   - Média de tempo por visita
   - KM percorrido

3. **Status de Empresas** (`status_empresas`)
   - Frequência de visitas
   - Última visita
   - Status atual

4. **Análise por Região** (`analise_regiao`)
   - Agrupamento por cidade/estado
   - Distribuição de visitas

5. **KPI Mensais** (`kpi_mensal`)
   - Comparativos mês a mês
   - Tendências

---

## 10. Modo Offline e Sincronização

### 10.1 Arquitetura de Armazenamento Local

```
AsyncStorage (App)
├── @visitaspro:access_token       → String
├── @visitaspro:refresh_token      → String
├── @cache_/api/visitas/agenda/    → JSON (visitas)
├── @cache_/api/perguntas/         → JSON (perguntas)
├── @cache_/api/empresas/          → JSON (empresas)
├── @api_queue                      → JSON (fila offline)
├── @visitaspro:jornada_estado     → JSON (jornada)
└── @visitaspro:jornada_waypoints  → JSON (waypoints)
```

### 10.2 Fluxo de Requisição Offline

```
User tenta ação (check-in, relatório)
      │
      ▼
┌──────────────────────┐
│ Conectividade OK?    │
└────┬────┬────────────┘
     │✓   │✗
     │    └─→ ┌─────────────────────┐
     │        │ Salvar em Fila      │
     │        │ addToQueue()        │
     │        └────┬────────────────┘
     │             │
     │      ┌──────▼──────────────┐
     │      │ Alert "Offline"     │
     │      │ "Enviado depois"    │
     │      └──────────────────────┘
     │
     ▼
┌───────────────────────┐
│ Fazer requisição HTTP │
└────┬────┬────────────┘
     │✓   │✗ (erro)
     │    └─────→ ┌──────────────────┐
     │            │ ✗ Conectividade? │
     │            │ → Fila           │
     │            │ ✓ Erro 4XX/5XX?  │
     │            │ → Fila           │
     │            └──────────────────┘
     │
     ▼
┌────────────────────────┐
│ Sucesso (2XX/3XX)      │
│ - Remove da fila       │
│ - Cache atualizado     │
│ - UI refresca          │
└────────────────────────┘
```

### 10.3 Processamento da Fila

**Quando Executa**:
- ✅ Ao abrir o app (se online)
- ✅ Pull-to-refresh
- ✅ Periodicamente (background, 5 min)
- ✅ Quando reconecta via listeners

**Lógica de Retry**:
```
Para cada item da fila:
  tentativas = 0
  Enquanto tentativas < 3:
    Tenta enviar para API
    Se sucesso:
      Remove da fila
      Quebra loop
    Senão:
      tentativas++
      Se tentativas < 3:
        Aguarda antes de retry
```

**Ordem de Processamento**:
- ✅ FIFO (First In, First Out)
- ✅ Mantém timestamp de quando foi enfileirado
- ✅ Pode ser prioritário (CHECKIN antes de RELATORIO)

### 10.4 Sincronização Bidirecional

**Download (Server → Device)**:
```
┌──────────────────────────┐
│ Dados do Servidor        │
│ - Agenda (visitas)       │
│ - Perguntas (questionário)
│ - Empresas (cadastro)    │
│ - Funcionários (contatos)│
└────────┬─────────────────┘
         │ via GET requests
         ▼
    ┌────────────────────────┐
    │ AsyncStorage (Cache)   │
    │ @cache_{endpoint}      │
    └────────────────────────┘
```

**Upload (Device → Server)**:
```
┌──────────────────────────┐
│ Dados do Device          │
│ - Check-in/out          │
│ - Relatório             │
│ - Fotos                 │
│ - KM da jornada         │
│ - Bug reports           │
└────────┬─────────────────┘
         │ via POST/PATCH requests
         ▼
    ┌────────────────────────┐
    │ API Django/DRF         │
    │ Validação + Persistência
    └────────────────────────┘
```

### 10.5 Conflitos e Resoluções

**Cenário 1: Múltiplos Check-ins Offline**
- ✅ Apenas 1 check-in por visita permitido
- ✅ Se já existe, rejeita 2º

**Cenário 2: Check-out antes de Check-in**
- ✅ Backend rejeita com erro 400
- ✅ Fila mantém item, tenta novamente

**Cenário 3: Dados Desatualizados**
- ✅ Cache válido por sessão (enquanto app aberto)
- ✅ Pull-to-refresh força atualização
- ✅ Ao reabrir app, sincroniza automaticamente

---

## 11. Validações e Restrições

### 11.1 Validações de Entrada

| Campo | Regra | Erro |
|-------|-------|------|
| `username` | Único, 150 chars max | "Usuário já existe" |
| `email` | Formato valid | "Email inválido" |
| `cnpj_cpf` | Máx 18 chars | - |
| `telefone` | Máx 20 chars | - |
| `latitude` | Parseável como float | "Coordenada inválida" |
| `longitude` | Parseável como float | "Coordenada inválida" |
| `data` | Formato YYYY-MM-DD | - |
| `horario` | Formato HH:MM:SS | - |
| `assinatura` | Base64 válido | "Assinatura inválida" |
| `resposta_texto` | Máx 255 chars | - |
| `resposta_numero` | Parseável como float | "Deve ser número" |

### 11.2 Restrições de Negócio

| Regra | Validação | Ação |
|-------|-----------|------|
| Visita sem empresa | FK obrigatória | Rejeita |
| Assessor sem permissão | Verificar ownership | Rejeita (403) |
| Check-in fora raio 500m | Geofencing | Pede justificativa |
| Check-out sem check-in | Validar sequência | Rejeita (400) |
| Relatório sem assinatura | Obrigatório | Rejeita (400) |
| Mínimo uma pergunta | Validar quantidade | Rejeita (400) |
| KM sempre crescente | KM_novo > KM_atual | Ignora decrescente |
| Token expirado | JWT verificação | Redirect login |

### 11.3 Limites de Taxa (Rate Limiting)

**Não implementado no backend**:
- ⚠️ Recomendação: Adicionar rate limit para produção
- ⚠️ Sugestão: 100 requisições/hora por usuário

**Timeout de Requisição**:
- ✅ 10 segundos por requisição HTTP (hardcoded no app)

---

## 12. Tratamento de Erros

### 12.1 Erros HTTP e Tratamento

| Status | Cenário | Ação no App |
|--------|---------|-----------|
| 401 | Token inválido/expirado | Limpa tokens, redireciona login |
| 403 | Sem permissão | Alert "Acesso negado" |
| 404 | Recurso não existe | Alert "Não encontrado" |
| 400 | Dados inválidos | Exibe erro do servidor |
| 500 | Erro interno | Alert + sugestão redirecionar |
| 503 | Serviço indisponível | Fallback offline |
| Network | Sem conexão | Fila + Alert "Modo Offline" |

### 12.2 Erros de Geolocalização

| Erro | Causa | Solução |
|------|-------|--------|
| Permission denied | Permissão GPS negada | Solicitar novamente |
| Position unavailable | GPS não disponível | Tentar novamente |
| Timeout | GPS demorando muito | Usar dados em cache |
| No position | Fora de área com GPS | Permitir justificativa |

### 12.3 Erros de Validação Customizados

**Geofencing**:
```json
{
  "error": "Você está a 850 metros da empresa. Para continuar, forneça uma justificativa."
}
```

**Assinatura Obrigatória**:
```json
{
  "error": "A assinatura da visita é obrigatória."
}
```

**Permissão Insuficiente**:
```json
{
  "error": "Visita não encontrada.",
  "detail": "Você não tem permissão para acessar esta visita."
}
```

### 12.4 Relatório de Bugs

**Fluxo de Report**:
```
User clica "Reportar Bug"
      │
      ▼
┌──────────────────────┐
│ Modal:               │
│ Descrição + Device  │
└────┬─────────────────┘
     │
     ▼
┌──────────────────────────────┐
│ POST /api/bugs/              │
│ {                            │
│   usuario: current_user,     │
│   descricao: "...",          │
│   device_info: "Android 14"  │
│ }                            │
└──────┬───────────────────────┘
       │
       ▼
    ┌────────────────┐
    │ Alert Sucesso  │
    │ "Obrigado!"    │
    └────────────────┘
```

**Campos do Report**:
- `usuario`: Automático (from request.user)
- `descricao`: Texto livre (máx 1000 chars recomendado)
- `device_info`: SO + modelo (ex: "iPhone 14 Pro, iOS 17")
- `resolvido`: Inicialmente False
- `criado_em`: Automático (timestamp)

---

## 13. Sumário das Regras de Negócio Críticas

### 🔴 CRÍTICAS (Bloqueantes)

1. **Autenticação JWT Obrigatória**: Todo acesso ao mobile requer token válido
2. **Geofencing 500m**: Check-in fora do raio exige justificativa
3. **Assinatura Opcional**: A visita pode ser finalizada sem assinatura
4. **Check-in Antes de Perguntas**: Deve fazer check-in primeiro
5. **Ownership de Visita**: Apenas assessor responsável pode editar
6. **KM Sempre Crescente**: Não aceita valores decrescentes

### 🟡 IMPORTANTES (Impactam UX)

7. **Modo Offline com Fila**: Requisições offline são enfileiradas
8. **Retry Automático**: Max 3 tentativas por item da fila
9. **Cache Local**: Dados sincronizados são cacheados
10. **Rastreamento GPS Periódico**: 5 minutos de intervalo
11. **Distância Mínima 5m**: Ignora movimentos menores
12. **Pull-to-Refresh**: Força sincronização manual

### 🟢 SECUNDÁRIAS (Otimizações)

13. Geocodificação automática via CEP
14. Conversão de empresas (N → A) registra data
15. Limite de 200 waypoints por jornada
16. Orientação horizontal para assinatura
17. FormData para upload de fotos/arquivos
18. Permissão dinâmica de assessores por empresa

---

## 14. Decisões Arquiteturais

### Por que React Native + Expo?
- ✅ Código único para iOS e Android
- ✅ Rápido desenvolvimento e deployment
- ✅ Over-the-air updates (Expo Updates)
- ✅ Suporte nativo a GPS, câmera, AsyncStorage

### Por que Django REST Framework no Backend?
- ✅ Validação automática de serializers
- ✅ Authentication/permissions robustas (SimpleJWT)
- ✅ Admin automático customizável (Django Admin)
- ✅ ORM poderoso (querysets otimizados)
- ✅ Documentação automática (Swagger/DRF)

### Por que AsyncStorage para Cache?
- ✅ Simples e sem dependências
- ✅ Suporta operação offline
- ✅ Persistência de tokens
- ✅ Rápido para dados pequenos/médios

### Por que Fila de Sincronização?
- ✅ Garante coleta de dados mesmo sem internet
- ✅ Retry automático minimiza perda de dados
- ✅ Reduz carga de requisições simultâneas
- ✅ User experience melhorada (não trava esperando rede)

---

## 15. Fluxo Completo de Uso (Exemplo Prático)

### Cenário: Consultor visitando empresa sem internet

**Manhã - Com Internet**:
1. App abre → Sincroniza agenda e perguntas
2. Agenda mostra visitas do dia (cached)
3. Consultor navega até empresa

**Na Empresa - Sem Internet**:
4. Clica "Check-in"
   - GPS captura localização
   - Distância 450m (dentro do raio) ✅
   - POST /api/visitas/{id}/checkin/ → **Fila**
5. Responde perguntas offline
6. Fotografa 3 evidências
7. Captura assinatura do responsável
8. Clica "Finalizar"
   - Check-out (POST) → **Fila**
   - Relatório + fotos (POST + FormData) → **Fila**
   - Alert: "📶 Salvo Offline. Enviado quando online"

**Volta para Base - Com Internet**:
9. Reconecta à rede
10. Background sync dispara
11. Fila processa 3 itens:
    - Check-in: ✅ Sucesso
    - Check-out: ✅ Sucesso
    - Relatório: ✅ Sucesso (com fotos)
12. Itens removidos da fila
13. UI atualiza (visita agora em "realizada")

**Backend Confirma**:
- Visita no status "realizada"
- Check-in/out com GPS registrado
- 3 fotos armazenadas
- Respostas do questionário salvas
- Assinatura Base64 armazenada

---

## 16. Recomendações de Segurança

### ✅ Implementado
- JWT com tokens com expiração
- Validação de ownership por endpoint
- HTTPS obrigatório (recomendado)
- Sem armazenamento de senha (JWT)
- CORS configurado no backend

### ⚠️ Recomendado para Produção
- Rate limiting por IP/usuário
- Refresh token rotation
- Logging de auditoria detalhado
- Backup diário do banco
- Monitoramento de requisições anormais
- Validação de dados más-formados mais rigorosa
- Criptografia de dados sensíveis (fotos, assinaturas)

---

## 17. Métricas e KPIs Disponíveis

### No Painel Admin

```python
GeradorRelatorios().gerar_resumo_geral() retorna:
{
  'total_visitas': int,
  'visitas_realizadas': int,
  'visitas_agendadas': int,
  'visitas_canceladas': int,
  'total_empresas': int,
  'empresas_ativas': int,
  'empresas_inativas': int,
  'empresas_negociacao': int,
  'taxa_conversao_percentual': float,  # N → A
  'media_visitas_por_empresa': float,
  'total_assessores': int,
  'distancia_media_percorrida': float,  # km
  'periodo': {
    'data_inicio': str,
    'data_fim': str,
    'dias': int
  }
}
```

---

## 18. Glossário

| Termo | Definição |
|-------|-----------|
| **Assessor** | Consultor que realiza visitas (marca de usuário `is_assessor=True`) |
| **Admin** | Administrador local (marca `is_admin=True`) |
| **Geofencing** | Verificação de localização dentro de raio (500m) |
| **JWT** | JSON Web Token (autenticação stateless) |
| **Jornada** | Período de trabalho diário com rastreamento de KM |
| **Waypoint** | Ponto geográfico registrado durante jornada |
| **Fila Offline** | Items pendentes quando sem internet |
| **Haversine** | Fórmula de cálculo de distância entre coordenadas |
| **Base64** | Codificação de assinatura para armazenamento |
| **FormData** | Formato para upload de múltiplos arquivos |
| **Taxa de Conversão** | % de empresas que mudaram de "Em Negociação" para "Ativa" |

---

## 19. Contato e Suporte

**Desenvolvedor Backend**: Django + DRF  
**Desenvolvedor Frontend (Web)**: Django Templates  
**Desenvolvedor Mobile**: React Native + Expo  
**Data de Documentação**: 5 de Maio de 2026  
**Versão**: 1.0

---

**Fim da Documentação** 📄
