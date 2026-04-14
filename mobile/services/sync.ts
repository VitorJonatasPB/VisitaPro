/**
 * services/sync.ts
 * Serviço central de sincronização.
 * Orquestra a busca de dados da API e o envio da fila de pendências.
 */

import NetInfo from '@react-native-community/netinfo';
import {
  fetchAgenda,
  fetchPerguntas,
  enviarRelatorio,
  realizarCheckin,
  realizarCheckout,
} from './api';
import {
  salvarAgendaLocal,
  salvarPerguntasLocal,
  carregarFila,
  removerDaFila,
  atualizarTentativas,
} from './storage';

const MAX_TENTATIVAS = 3;

/**
 * Sincroniza dados do servidor para o dispositivo (Download).
 * Ideal para chamar ao abrir o app ou ao puxar para atualizar.
 */
export async function sincronizarDoServidor(): Promise<boolean> {
  const netInfo = await NetInfo.fetch();
  if (!netInfo.isConnected) {
    console.log('[Sync] Sem conexão. Usando dados locais.');
    return false;
  }

  try {
    console.log('[Sync] Baixando dados do servidor...');
    const [agenda, perguntas] = await Promise.all([
      fetchAgenda(),
      fetchPerguntas(),
    ]);
    await salvarAgendaLocal(agenda);
    await salvarPerguntasLocal(perguntas);
    console.log(`[Sync] Dados atualizados: ${agenda.length} visitas, ${perguntas.length} perguntas.`);
    return true;
  } catch (error) {
    console.error('[Sync] Falha ao sincronizar com servidor:', error);
    return false;
  }
}

/**
 * Processa a fila de envios pendentes (Upload).
 * Ideal para chamar quando a conexão for restaurada.
 */
export async function processarFilaDeSincronismo(): Promise<void> {
  const netInfo = await NetInfo.fetch();
  if (!netInfo.isConnected) {
    console.log('[Sync] Sem conexão. Fila não processada.');
    return;
  }

  const fila = await carregarFila();
  if (fila.length === 0) {
    console.log('[Sync] Fila vazia, nada para enviar.');
    return;
  }

  console.log(`[Sync] Processando ${fila.length} item(ns) na fila...`);

  for (const item of fila) {
    if (item.tentativas >= MAX_TENTATIVAS) {
      console.warn(`[Sync] Item ${item.id} excedeu máximo de tentativas. Pulando.`);
      continue;
    }

    try {
      // Envia check-in se pendente
      if (item.checkin) {
        await realizarCheckin(item.visitaId, item.checkin.lat, item.checkin.lng);
      }
      // Envia check-out se pendente
      if (item.checkout) {
        await realizarCheckout(item.visitaId, item.checkout.lat, item.checkout.lng);
      }
      // Envia respostas do relatório se pendentes
      if (item.respostas.length > 0) {
        await enviarRelatorio(item.visitaId, item.respostas, item.assinatura);
      }

      await removerDaFila(item.id);
      console.log(`[Sync] Item ${item.id} enviado com sucesso.`);
    } catch (error) {
      console.error(`[Sync] Falha ao enviar item ${item.id}:`, error);
      await atualizarTentativas(item.id);
    }
  }
}

/**
 * Inicia o listener de conectividade.
 * Deve ser chamado 1 vez na raiz do app (_layout.tsx).
 * Toda vez que o celular reconectar, processa a fila automaticamente.
 */
export function iniciarListenerDeConectividade() {
  NetInfo.addEventListener((state) => {
    if (state.isConnected) {
      console.log('[Sync] Conexão restaurada! Processando fila...');
      processarFilaDeSincronismo();
    }
  });
}
