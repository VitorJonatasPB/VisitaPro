/**
 * services/storage.ts
 * Camada de persistência local usando AsyncStorage.
 * Salva a agenda, as perguntas e a fila de sincronização no dispositivo.
 */

import AsyncStorage from '@react-native-async-storage/async-storage';
import { VisitaAPI, PerguntaAPI, RespostaPayload } from './api';

const KEYS = {
  agenda: '@rota99:agenda',
  perguntas: '@rota99:perguntas',
  filaSincronismo: '@rota99:fila_sincronismo',
};

// ---------- Agenda ----------

export async function salvarAgendaLocal(visitas: VisitaAPI[]): Promise<void> {
  await AsyncStorage.setItem(KEYS.agenda, JSON.stringify(visitas));
}

export async function carregarAgendaLocal(): Promise<VisitaAPI[]> {
  const json = await AsyncStorage.getItem(KEYS.agenda);
  return json ? JSON.parse(json) : [];
}

// ---------- Perguntas ----------

export async function salvarPerguntasLocal(perguntas: PerguntaAPI[]): Promise<void> {
  await AsyncStorage.setItem(KEYS.perguntas, JSON.stringify(perguntas));
}

export async function carregarPerguntasLocal(): Promise<PerguntaAPI[]> {
  const json = await AsyncStorage.getItem(KEYS.perguntas);
  return json ? JSON.parse(json) : [];
}

// ---------- Fila de Sincronismo ----------

export interface ItemFila {
  id: string;         // UUID para identificar unicamente o item
  visitaId: number;
  respostas: RespostaPayload[];
  assinatura?: string;
  checkin?: { lat: number; lng: number };
  checkout?: { lat: number; lng: number };
  tentativas: number;
  criadoEm: string;   // ISO Date string
}

export async function adicionarNaFila(item: Omit<ItemFila, 'id' | 'tentativas' | 'criadoEm'>): Promise<void> {
  const fila = await carregarFila();
  const novoItem: ItemFila = {
    ...item,
    id: Math.random().toString(36).substring(2), // ID simples
    tentativas: 0,
    criadoEm: new Date().toISOString(),
  };
  fila.push(novoItem);
  await AsyncStorage.setItem(KEYS.filaSincronismo, JSON.stringify(fila));
}

export async function carregarFila(): Promise<ItemFila[]> {
  const json = await AsyncStorage.getItem(KEYS.filaSincronismo);
  return json ? JSON.parse(json) : [];
}

export async function removerDaFila(itemId: string): Promise<void> {
  const fila = await carregarFila();
  const filaAtualizada = fila.filter((item) => item.id !== itemId);
  await AsyncStorage.setItem(KEYS.filaSincronismo, JSON.stringify(filaAtualizada));
}

export async function atualizarTentativas(itemId: string): Promise<void> {
  const fila = await carregarFila();
  const filaAtualizada = fila.map((item) =>
    item.id === itemId ? { ...item, tentativas: item.tentativas + 1 } : item
  );
  await AsyncStorage.setItem(KEYS.filaSincronismo, JSON.stringify(filaAtualizada));
}
