import * as Location from 'expo-location';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { sincronizarJornadaKm } from './api';

// Chave para armazenar a jornada atual offline
const JORNADA_STORAGE_KEY = '@visitaspro:jornada_estado';
const JORNADA_WAYPOINTS_KEY = '@visitaspro:jornada_waypoints';

export interface JornadaState {
  status: 'nao_iniciada' | 'em_andamento' | 'finalizada';
  km_total: number;
  last_lat?: number;
  last_lng?: number;
}

export interface Waypoint {
  lat: number;
  lng: number;
}

// Retorna o estado atual salvo da jornada
export async function getJornadaState(): Promise<JornadaState> {
  try {
    const data = await AsyncStorage.getItem(JORNADA_STORAGE_KEY);
    if (data) {
      return JSON.parse(data);
    }
  } catch (e) {
    console.error('Erro ao ler estado da jornada', e);
  }
  return { status: 'nao_iniciada', km_total: 0 };
}

export async function saveJornadaState(state: JornadaState) {
  await AsyncStorage.setItem(JORNADA_STORAGE_KEY, JSON.stringify(state));
}

export async function clearJornadaState() {
  await AsyncStorage.removeItem(JORNADA_STORAGE_KEY);
}

// Waypoints: pontos da trajetória para o mapa
export async function getWaypoints(): Promise<Waypoint[]> {
  try {
    const data = await AsyncStorage.getItem(JORNADA_WAYPOINTS_KEY);
    if (data) return JSON.parse(data);
  } catch (e) {}
  return [];
}

export async function addWaypoint(lat: number, lng: number) {
  try {
    const waypoints = await getWaypoints();
    // Guarda no máximo 200 pontos para não explodir o armazenamento
    if (waypoints.length >= 200) waypoints.shift();
    waypoints.push({ lat, lng });
    await AsyncStorage.setItem(JORNADA_WAYPOINTS_KEY, JSON.stringify(waypoints));
  } catch (e) {}
}

export async function clearWaypoints() {
  await AsyncStorage.removeItem(JORNADA_WAYPOINTS_KEY);
}

// Gera a URL do Google Static Maps com a rota desenhada
export async function gerarUrlMapaTrajetoria(): Promise<string | null> {
  const waypoints = await getWaypoints();
  if (waypoints.length < 2) return null;

  // Amostra até 20 pontos para não estourar o limite de URL da API
  const step = Math.ceil(waypoints.length / 20);
  const pontos = waypoints.filter((_, i) => i % step === 0);

  const path = pontos.map(p => `${p.lat},${p.lng}`).join('|');
  const inicio = `${waypoints[0].lat},${waypoints[0].lng}`;
  const fim = `${waypoints[waypoints.length - 1].lat},${waypoints[waypoints.length - 1].lng}`;

  // Usa a URL do Google Maps no navegador (não precisa de API key)
  const url = `https://www.google.com/maps/dir/${encodeURIComponent(inicio)}/${encodeURIComponent(fim)}`;
  return url;
}

// Helper: Distância de Haversine (em metros)
export function calcularDistanciaMetros(lat1: number, lng1: number, lat2: number, lng2: number): number {
  const R = 6371e3; // raio da terra em metros
  const toRad = (v: number) => (v * Math.PI) / 180;
  const dLat = toRad(lat2 - lat1);
  const dLng = toRad(lng2 - lng1);
  const a = Math.sin(dLat / 2) ** 2 +
            Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLng / 2) ** 2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

let locationSubscription: Location.LocationSubscription | null = null;
let syncInterval: any = null;

// Inicia o rastreamento em primeiro plano (quando o app tá ativo)
export async function startTrackingJornada(onUpdateKm: (km: number) => void) {
  const { status } = await Location.requestForegroundPermissionsAsync();
  if (status !== 'granted') {
    throw new Error('Permissão de localização negada');
  }

  // Parar qualquer rastreio anterior
  await stopTrackingJornada();

  // Watch position config: atualizar a cada 50 metros ou a cada 30 segundos
  locationSubscription = await Location.watchPositionAsync(
    {
      accuracy: Location.Accuracy.High,
      timeInterval: 30000,
      distanceInterval: 50, // só atualiza se mover >50m para poupar bateria/cálculo
    },
    async (location) => {
      const state = await getJornadaState();
      
      if (state.status === 'em_andamento') {
        const lat = location.coords.latitude;
        const lng = location.coords.longitude;
        
        if (state.last_lat && state.last_lng) {
          const distancia = calcularDistanciaMetros(state.last_lat, state.last_lng, lat, lng);
          
          // Somar ao KM se a distância for razoável (ignorar "pulos" absurdos de GPS > 10km num tick normal)
          if (distancia > 5 && distancia < 10000) {
            state.km_total += (distancia / 1000); // converte pra km
          }
        }
        
        state.last_lat = lat;
        state.last_lng = lng;
        
        await saveJornadaState(state);
        // Registrar ponto da trajetória
        await addWaypoint(lat, lng);
        onUpdateKm(state.km_total);
      }
    }
  );

  // Intervalo para sincronizar com o backend periodicamente (a cada 5 minutos)
  syncInterval = setInterval(async () => {
    const state = await getJornadaState();
    if (state.status === 'em_andamento' && state.km_total > 0) {
      try {
        await sincronizarJornadaKm(state.km_total);
      } catch (e) {
        // Ignora erro de rede, apenas tenta de novo na próxima vez
      }
    }
  }, 5 * 60 * 1000);
}

export async function stopTrackingJornada() {
  if (locationSubscription) {
    locationSubscription.remove();
    locationSubscription = null;
  }
  if (syncInterval) {
    clearInterval(syncInterval);
    syncInterval = null;
  }
}
