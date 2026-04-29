import AsyncStorage from '@react-native-async-storage/async-storage';
import { router } from 'expo-router';
import { addToQueue, getQueue } from './queue';

export const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL || 'https://novovisitaspro-production.up.railway.app';

export const ENDPOINTS = {
  token: '/api/token/',
  tokenRefresh: '/api/token/refresh/',
  agenda: '/api/visitas/agenda/',
  agendaMes: '/api/visitas/mes/',
  novoAgendamento: '/api/visitas/novo/',
  visita: (id: number) => `/api/visitas/${id}/`,
  perguntas: '/api/perguntas/',
  checkin: (id: number) => `/api/visitas/${id}/checkin/`,
  checkout: (id: number) => `/api/visitas/${id}/checkout/`,
  responder: (id: number) => `/api/visitas/${id}/responder/`,
  calendario: '/api/visitas/calendario/',
  contatoes: (id: number) => `/api/visitas/${id}/contatoes/`,
  perfil: '/api/users/me/',
  bugs: '/api/bugs/',
  empresasGlobal: '/api/empresas/',
  contatoesGlobal: '/api/contatoes/',
};

// ---------- Helpers de Token ----------

export async function getAccessToken(): Promise<string | null> {
  return AsyncStorage.getItem('@visitaspro:access_token');
}

export async function saveTokens(access: string, refresh: string) {
  await AsyncStorage.setItem('@visitaspro:access_token', access);
  await AsyncStorage.setItem('@visitaspro:refresh_token', refresh);
}

export async function clearTokens() {
  await AsyncStorage.removeItem('@visitaspro:access_token');
  await AsyncStorage.removeItem('@visitaspro:refresh_token');
}

// ---------- Requisição Base ----------

export async function request<T>(
  endpoint: string,
  method: 'GET' | 'POST' | 'PATCH' | 'PUT' = 'GET',
  body?: object | FormData
): Promise<T> {
  const token = await getAccessToken();
  const headers: Record<string, string> = {};
  
  // Se não for FormData, envia JSON
  if (!(body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  // Timeout de 10 segundos para não ficar carregando infinitamente
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 10000);

  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method,
      headers,
      body: body instanceof FormData ? body : (body ? JSON.stringify(body) : undefined),
      signal: controller.signal as RequestInit['signal'],
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      if (response.status === 401) {
        // Token morreu ou foi invalidado no servidor
        await clearTokens();
        try {
          router.replace('/');
        } catch(e) {}
      }
      const errorData = await response.json().catch(() => ({}));
      // Retorna a mensagem de erro específica do Django ou o status HTTP
      const message = errorData.detail || errorData.error || `Erro no servidor (Status ${response.status})`;
      throw new Error(message);
    }

    const resData = await response.json();
    if (method === 'GET') {
      await AsyncStorage.setItem(`@cache_${endpoint}`, JSON.stringify(resData));
    }
    return resData as T;
  } catch (error: any) {
    clearTimeout(timeoutId);
    if (error.name === 'AbortError' || error.message?.includes('Network request failed') || error.message?.includes('Failed to fetch')) {
      error.isNetworkError = true;
      if (method === 'GET') {
        const cached = await AsyncStorage.getItem(`@cache_${endpoint}`);
        if (cached) {
          console.log(`[Cache] Returning offline data for ${endpoint}`);
          return JSON.parse(cached) as T;
        }
      }
    }
    // Repassa o erro estourado acima ou problema de rede mantendo a flag
    if (error.message?.includes('Network request failed') || error.message?.includes('Failed to fetch')) {
      const netErr = new Error('Não foi possível conectar ao servidor. Verifique a URL da API ou sua rede.');
      (netErr as any).isNetworkError = true;
      throw netErr;
    }
    throw error;
  }
}

// ---------- Autenticação ----------

export async function login(username: string, password: string): Promise<boolean> {
  const data = await request<{ access: string; refresh: string }>(
    ENDPOINTS.token,
    'POST',
    { username, password }
  );
  await saveTokens(data.access, data.refresh);
  return true;
}

// ---------- Agenda ----------

export interface EmpresaAPI {
  id: number;
  nome: string;
  regiao_nome: string;
  telefone: string | null;
  email: string | null;
  status: string;
  frequencia_recomendada_dias: number;
  ultima_visita: string | null;
  latitude: string | null;
  longitude: string | null;
}

export interface VisitaAPI {
  id: number;
  empresa_nome: string;
  empresa?: EmpresaAPI;
  empresa_lat?: string | null;
  empresa_lng?: string | null;
  horario: string;
  data: string;
  status: string;
  checkin_time: string | null;
  checkout_time: string | null;
}

export async function fetchAgenda(dataIso?: string): Promise<VisitaAPI[]> {
  const url = dataIso ? `${ENDPOINTS.agenda}?data=${dataIso}` : ENDPOINTS.agenda;
  const list = await request<VisitaAPI[]>(url, 'GET');
  return patchListWithQueue(list);
}

export async function fetchVisitasMes(ano: number, mes: number): Promise<VisitaAPI[]> {
  const url = `${ENDPOINTS.agendaMes}?ano=${ano}&mes=${mes}`;
  const list = await request<VisitaAPI[]>(url, 'GET');
  return patchListWithQueue(list);
}

async function patchListWithQueue(list: VisitaAPI[]): Promise<VisitaAPI[]> {
  try {
      const queue = await getQueue();
      if (queue.length === 0) return list;
      return list.map(visita => {
         const myQueue = queue.filter(q => q.endpoint.includes(`/api/visitas/${visita.id}/`));
         let updated = { ...visita };
         myQueue.forEach(qItem => {
             if (qItem.type === 'CHECKIN') updated.checkin_time = qItem.payload.checkin_time;
             else if (qItem.type === 'CHECKOUT') {
                 updated.checkout_time = qItem.payload.checkout_time;
                 updated.status = 'realizada';
             }
         });
         return updated;
      });
  } catch(e) {
      return list;
  }
}

export async function criarAgendamento(empresa_id: number, data: string, horario: string) {
  return request(ENDPOINTS.novoAgendamento, 'POST', { empresa_id, data, horario });
}

export async function fetchVisitaById(id: number): Promise<VisitaAPI> {
  let visita: VisitaAPI | null = null;
  try {
    visita = await request<VisitaAPI>(ENDPOINTS.visita(id), 'GET');
  } catch (err: any) {
    if (err.isNetworkError || err.message?.includes('servidor')) {
      const dt = new Date();
      const mesEndpoint = ENDPOINTS.agendaMes + `?ano=${dt.getFullYear()}&mes=${dt.getMonth() + 1}`;
      const cachedAgenda = await AsyncStorage.getItem(`@cache_${mesEndpoint}`);
      if (cachedAgenda) {
        const visitas = JSON.parse(cachedAgenda) as VisitaAPI[];
        const match = visitas.find(v => v.id === id);
        if (match) visita = match;
      }
    }
    if (!visita) throw err;
  }

  // Se achamos a visita (seja online ou pelo cache do mês), 
  // vamos injetar dados da Fila Offline que ainda não subiram pro Servidor!
  if (visita) {
    const queue = await getQueue();
    const myQueue = queue.filter(q => q.endpoint.includes(`/api/visitas/${id}/`));
    myQueue.forEach(qItem => {
      if (qItem.type === 'CHECKIN') {
        visita!.checkin_time = qItem.payload.checkin_time;
      } else if (qItem.type === 'CHECKOUT') {
        visita!.checkout_time = qItem.payload.checkout_time;
        visita!.status = 'realizada';
      }
    });
    return visita;
  }
  throw new Error("Visita não encontrada");
}

export async function fetchCalendarioVisitas(): Promise<string[]> {
  return request<string[]>(ENDPOINTS.calendario, 'GET');
}

// ---------- Perguntas ----------

export interface PerguntaAPI {
  id: number;
  texto: string;
  tipo_resposta: string;
  opcoes_resposta: string | null;
  fonte_dados?: string | null;
}

export async function fetchPerguntas(): Promise<PerguntaAPI[]> {
  return request<PerguntaAPI[]>(ENDPOINTS.perguntas);
}

// ---------- Check-in / Check-out ----------

export async function realizarCheckin(visitaId: number, lat: number, lng: number, justificativa?: string) {
  const payload: Record<string, string> = {
    checkin_lat: String(lat),
    checkin_lng: String(lng),
    checkin_time: new Date().toISOString(),
  };
  if (justificativa) {
    payload.justificativa_distancia = justificativa;
  }
  try {
    return await request(ENDPOINTS.checkin(visitaId), 'POST', payload);
  } catch (err: any) {
    if (err.isNetworkError) {
      await addToQueue('CHECKIN', ENDPOINTS.checkin(visitaId), 'POST', payload);
      return { offline: true, message: 'Salvo offline. Será sincronizado automaticamente...' };
    }
    throw err;
  }
}

export async function realizarCheckout(visitaId: number, lat: number, lng: number) {
  const payload = {
    checkout_lat: String(lat),
    checkout_lng: String(lng),
    checkout_time: new Date().toISOString(),
  };
  try {
    return await request(ENDPOINTS.checkout(visitaId), 'POST', payload);
  } catch (err: any) {
    if (err.isNetworkError) {
      await addToQueue('CHECKOUT', ENDPOINTS.checkout(visitaId), 'POST', payload);
      return { offline: true, message: 'Salvo offline. Será sincronizado automaticamente...' };
    }
    throw err;
  }
}

// ---------- Enviar Respostas ----------

export interface RespostaPayload {
  pergunta: number;
  resposta: string;
}

export interface ContatoAPI {
  id: number;
  nome: string;
  matricula: string | null;
  empresa_nome?: string;
  telefone?: string | null;
  email?: string | null;
}

export async function fetchContatoesEmpresa(visitaId: number): Promise<ContatoAPI[]> {
  return request<ContatoAPI[]>(ENDPOINTS.contatoes(visitaId), 'GET');
}

export async function enviarRelatorio(
  visitaId: number, 
  respostas: RespostaPayload[], 
  assinatura?: string, 
  contatoes?: number[],
  fotos?: string[]
) {
  const formData = new FormData();
  
  // O Django pode receber string JSON em um campo do formulário multipart chamado 'payload'
  const payloadStr = JSON.stringify({
    respostas,
    assinatura,
    contatoes_atendidos: contatoes
  });
  formData.append('payload', payloadStr);

  // Anexar array de imagens (fotos)
  if (fotos && fotos.length > 0) {
    fotos.forEach((uri, i) => {
      const filename = uri.split('/').pop() || `foto_${i}.jpg`;
      formData.append('fotos', {
        uri,
        name: filename,
        type: 'image/jpeg'
      } as any);
    });
  }

  // Se tem fotos, manda FormData. Se não, manda o objeto JSON comum do payload.
  const hasFotos = fotos && fotos.length > 0;
  const finalPayload = hasFotos ? formData : { respostas, assinatura, contatoes_atendidos: contatoes };

  try {
    return await request(ENDPOINTS.responder(visitaId), 'POST', finalPayload);
  } catch (err: any) {
    // Para FormData não conseguimos serializar com JSON puro na queue facilmente no AsyncStorage
    // O ideal offline com imagens é salvar o URI. Como estamos em adaptação simples:
    if (err.isNetworkError && !hasFotos) {
      await addToQueue('RELATORIO', ENDPOINTS.responder(visitaId), 'POST', finalPayload);
      return { offline: true, message: 'Salvo offline. Será sincronizado automaticamente...' };
    } else if (err.isNetworkError && hasFotos) {
       throw new Error('Fotos não podem ser salvas offline ainda. Aguarde conexão ou envie sem fotos.');
    }
    throw err;
  }
}

// ---------- Perfil do Usuário ----------

export interface UserAPI {
  id: number;
  username: string;
  first_name: string;
  last_name: string;
  email: string;
  telefone: string | null;
  foto: string | null;
}

export async function fetchPerfil(): Promise<UserAPI> {
  return request<UserAPI>(ENDPOINTS.perfil, 'GET');
}

export async function updatePerfil(data: Partial<UserAPI>): Promise<UserAPI> {
  try {
    return await request<UserAPI>(ENDPOINTS.perfil, 'PATCH', data);
  } catch (err: any) {
    if (err.isNetworkError) {
      await addToQueue('PERFIL' as any, ENDPOINTS.perfil, 'PATCH', data);
      return { offline: true, message: 'Alterações no perfil salvas offline.' } as unknown as UserAPI;
    }
    throw err;
  }
}

export async function uploadFotoPerfil(photoUri: string, filename: string): Promise<UserAPI> {
  const formData = new FormData();
  formData.append('foto', {
    uri: photoUri,
    name: filename,
    type: 'image/jpeg'
  } as any);

  return request<UserAPI>(ENDPOINTS.perfil, 'PATCH', formData);
}

// ---------- Reportar Erros ----------

export interface BugReportAPI {
  descricao: string;
  device_info?: string;
}

export async function reportBug(data: BugReportAPI): Promise<any> {
  try {
    return await request(ENDPOINTS.bugs, 'POST', data);
  } catch (err: any) {
    if (err.isNetworkError) {
      await addToQueue('BUG', ENDPOINTS.bugs, 'POST', data);
      return { offline: true, message: 'Bug salvo para envio remoto.' };
    }
    throw err;
  }
}

// ---------- Empresas e Contatoes Globais ----------

export async function fetchEmpresasGlobais(): Promise<EmpresaAPI[]> {
  return request<EmpresaAPI[]>(ENDPOINTS.empresasGlobal, 'GET');
}

export async function fetchContatoesGlobais(): Promise<ContatoAPI[]> {
  return request<ContatoAPI[]>(ENDPOINTS.contatoesGlobal, 'GET');
}
