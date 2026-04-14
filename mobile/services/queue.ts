import AsyncStorage from '@react-native-async-storage/async-storage';
import NetInfo from '@react-native-community/netinfo';
import { request, ENDPOINTS } from './api';

const QUEUE_KEY = '@api_queue';

export interface QueueItem {
  id: string;
  endpoint: string;
  method: 'POST' | 'PUT' | 'PATCH';
  payload: any;
  timestamp: string;
  type: 'CHECKIN' | 'CHECKOUT' | 'RELATORIO' | 'BUG';
}

export async function addToQueue(type: QueueItem['type'], endpoint: string, method: QueueItem['method'], payload: any) {
  try {
    const queueData = await AsyncStorage.getItem(QUEUE_KEY);
    const queue: QueueItem[] = queueData ? JSON.parse(queueData) : [];

    const newItem: QueueItem = {
      id: Date.now().toString() + Math.random().toString(36).substring(7),
      type,
      endpoint,
      method,
      payload,
      timestamp: new Date().toISOString(),
    };

    queue.push(newItem);
    await AsyncStorage.setItem(QUEUE_KEY, JSON.stringify(queue));
    console.log(`[Queue] Added ${type} to offline queue.`);
    return newItem;
  } catch (error) {
    console.error('[Queue] Error adding to queue', error);
  }
}

export async function getQueue(): Promise<QueueItem[]> {
  try {
    const queueData = await AsyncStorage.getItem(QUEUE_KEY);
    return queueData ? JSON.parse(queueData) : [];
  } catch (error) {
    console.error('[Queue] Error getting queue', error);
    return [];
  }
}

export async function processQueue() {
  const isConnected = (await NetInfo.fetch()).isConnected;
  if (!isConnected) {
    console.log('[Queue] Cannot process queue. No internet connection.');
    return;
  }

  const queue = await getQueue();
  if (queue.length === 0) return;

  console.log(`[Queue] Processing ${queue.length} items...`);
  const failedItems: QueueItem[] = [];

  for (const item of queue) {
    try {
      // Adicionamos a flag is_offline_sync para o backend saber
      const payloadObj = typeof item.payload === 'string' ? item.payload : { ...item.payload, is_offline_sync: true, client_timestamp: item.timestamp };
      
      console.log(`[Queue] Syncing ${item.type} to ${item.endpoint}...`);
      await request(item.endpoint, item.method, payloadObj);
      console.log(`[Queue] Sync successful for ${item.type}`);
    } catch (e: any) {
      console.error(`[Queue] Sync failed for ${item.type}`, e);
      // Se o backend rejeitou frontalmente com 400, o payload está quebrado. 
      // Não repete infinitamente para não travar a fila.
      if (e.message && e.message.includes('400')) {
        console.warn(`[Queue] Discarding fatally rejected item: ${item.type}`);
      } else {
        failedItems.push(item);
      }
    }
  }

  // Update queue with only failed items left
  await AsyncStorage.setItem(QUEUE_KEY, JSON.stringify(failedItems));
}

// Hook para escutar mudanças de rede e processar fila
export function initQueueSyncListener() {
  const unsubscribe = NetInfo.addEventListener(state => {
    if (state.isConnected && state.isInternetReachable) {
      processQueue();
    }
  });
  return unsubscribe;
}
