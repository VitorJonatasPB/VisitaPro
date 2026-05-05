import React, { useState, useCallback } from 'react';
import { StyleSheet, Text, View, ScrollView, TouchableOpacity, Image, ActivityIndicator, RefreshControl, Modal, Pressable, Alert, Linking, BackHandler } from 'react-native';
import { useRouter, useFocusEffect } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Calendar, LocaleConfig } from 'react-native-calendars';
import { IconSymbol } from '@/components/ui/icon-symbol';
import { carregarAgendaLocal } from '@/services/storage';
import { sincronizarDoServidor } from '@/services/sync';
import { VisitaAPI, clearTokens, fetchPerfil, UserAPI, API_BASE_URL, fetchAgenda, fetchCalendarioVisitas, fetchVisitasMes, checkJornadaStatus, iniciarJornada, finalizarJornada } from '@/services/api';
import { getJornadaState, saveJornadaState, startTrackingJornada, stopTrackingJornada, JornadaState, gerarUrlMapaTrajetoria, clearWaypoints } from '@/services/location';
import * as Location from 'expo-location';

LocaleConfig.locales['pt-br'] = {
  monthNames: ['Janeiro','Fevereiro','Marco','Abril','Maio','Junho','Julho','Agosto','Setembro','Outubro','Novembro','Dezembro'],
  monthNamesShort: ['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez'],
  dayNames: ['Domingo','Segunda','Terca','Quarta','Quinta','Sexta','Sabado'],
  dayNamesShort: ['D','S','T','Q','Q','S','S'],
  today: 'Hoje'
};
LocaleConfig.defaultLocale = 'pt-br';

export default function AgendaScreen() {
  const router = useRouter();
  const [visitas, setVisitas] = useState<VisitaAPI[]>([]);
  const [user, setUser] = useState<UserAPI | null>(null);
  const [loading, setLoading] = useState(true);
  const [sincronizando, setSincronizando] = useState(false);
  const [offline, setOffline] = useState(false);
  const [menuVisible, setMenuVisible] = useState(false);

  // Pesquisa e Calendario
  const [searchText, setSearchText] = useState('');
  const [showCalendar, setShowCalendar] = useState(false);
  const [selectedDate, setSelectedDate] = useState<string>(new Date().toISOString().split('T')[0]);
  const [markedDates, setMarkedDates] = useState<Record<string, any>>({});
  
  // Filtro de Dashboard
  const [filterMode, setFilterMode] = useState<'diario' | 'mensal'>('diario');

  // Jornada
  const [jornada, setJornada] = useState<JornadaState>({ status: 'nao_iniciada', km_total: 0 });

  const hoje = new Date().toLocaleDateString('pt-BR', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
  });

  const hojeISO = new Date().toISOString().split('T')[0];
  const isHoje = selectedDate === hojeISO;

  const carregarDados = useCallback(async (forcarSinc = false) => {
    if (forcarSinc) setSincronizando(true);
    const conectado = await sincronizarDoServidor();
    setOffline(!conectado);
    try {
      if (conectado) {
        try {
          const dias = await fetchCalendarioVisitas();
          const marcas: Record<string, any> = {};
          dias.forEach(d => { marcas[d] = { marked: true, dotColor: '#3B82F6' }; });
          setMarkedDates(marcas);
          
          // Pre-fetch do mes atual para preencher nosso cache generico offline
          const dataAtual = new Date(selectedDate + 'T12:00:00');
          await fetchVisitasMes(dataAtual.getFullYear(), dataAtual.getMonth() + 1);
        } catch {}
        
        let agendaRemota = [];
        if (filterMode === 'mensal') {
          const dt = new Date(selectedDate + 'T12:00:00');
          agendaRemota = await fetchVisitasMes(dt.getFullYear(), dt.getMonth() + 1);
        } else {
          agendaRemota = await fetchAgenda(selectedDate);
        }
        setVisitas(agendaRemota);
      } else {
        // Se bateu sem conexao, tentaremos puxar do cache mensal que preenchemos via fetchVisitasMes
        const dt = new Date(selectedDate + 'T12:00:00');
        const monthData = await fetchVisitasMes(dt.getFullYear(), dt.getMonth() + 1);
        if (filterMode === 'diario') {
          setVisitas(monthData.filter(v => v.data === selectedDate));
        } else {
          setVisitas(monthData);
        }
      }
    } catch {
       // Em caso de erro extremo (nem cache mensal tem), tenta a base persistida antiga
       try {
         const agendaLocal = await carregarAgendaLocal();
         if (filterMode === 'diario') {
           setVisitas(agendaLocal.filter(v => v.data === selectedDate));
         } else {
           setVisitas(agendaLocal);
         }
       } catch {
         setVisitas([]);
       }
    } finally {
      setLoading(false);
      setSincronizando(false);
    }
  }, [selectedDate, filterMode]);

  const carregarUser = useCallback(async () => {
    try {
      const data = await fetchPerfil();
      setUser(data);
    } catch (e) {
      console.log('Erro ao carregar perfil', e);
    }
  }, []);

  const carregarJornada = useCallback(async () => {
    try {
      const jApi = await checkJornadaStatus();
      setJornada({ status: jApi.status, km_total: jApi.km_total || 0 });
      await saveJornadaState({ status: jApi.status, km_total: jApi.km_total || 0 });
      if (jApi.status === 'em_andamento') {
        startTrackingJornada((km) => setJornada(prev => ({ ...prev, km_total: km })));
      } else {
        stopTrackingJornada();
      }
    } catch {
      const jLocal = await getJornadaState();
      setJornada(jLocal);
      if (jLocal.status === 'em_andamento') {
        startTrackingJornada((km) => setJornada(prev => ({ ...prev, km_total: km })));
      }
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      carregarDados();
      carregarUser();
      carregarJornada();
    }, [carregarDados, carregarUser, carregarJornada])
  );

  const onRefresh = useCallback(async () => {
    carregarDados(true);
  }, [carregarDados]);


  const handleLogout = async () => {
    setMenuVisible(false);
    
    try {
      await stopTrackingJornada();
      await clearTokens();
      
      // Como o expo-router está travando a navegação na raiz, forçamos o fechamento do app
      Alert.alert(
        'Sessão Encerrada',
        'O aplicativo será fechado para aplicar a troca de conta.\n\nPor favor, abra-o novamente para fazer o novo login.',
        [{ text: 'Fechar App', onPress: () => BackHandler.exitApp() }]
      );
    } catch (e: any) {
      Alert.alert('Erro', e?.message || 'Erro ao sair');
    }
  };

  const handleIniciarJornada = async () => {
    try {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert('Atencao', 'Permissao de localizacao e necessaria para iniciar a jornada.');
        return;
      }
      const loc = await Location.getCurrentPositionAsync({ accuracy: Location.Accuracy.High });
      await iniciarJornada(loc.coords.latitude, loc.coords.longitude);

      const novoEstado: JornadaState = {
        status: 'em_andamento',
        km_total: 0,
        last_lat: loc.coords.latitude,
        last_lng: loc.coords.longitude
      };
      setJornada(novoEstado);
      await saveJornadaState(novoEstado);

      startTrackingJornada((km) => setJornada(prev => ({ ...prev, km_total: km })));
      Alert.alert('Jornada Iniciada', 'Dirija com seguranca! O aplicativo agora registrara a distancia percorrida.');
    } catch (e: any) {
      Alert.alert('Erro', e.message || 'Nao foi possivel iniciar a jornada agora.');
    }
  };

  const handleFinalizarJornada = async () => {
    Alert.alert(
      'Finalizar Jornada',
      `Total percorrido: ${jornada.km_total.toFixed(2)} km\n\nO que deseja fazer?`,
      [
        { text: 'Cancelar', style: 'cancel' },
        {
          text: 'Continuar Contando',
          onPress: () => {
            // Tracking ja ativo, apenas fecha o alerta
          }
        },
        {
          text: 'Finalizar Dia',
          style: 'destructive',
          onPress: async () => {
            try {
              const loc = await Location.getCurrentPositionAsync({ accuracy: Location.Accuracy.High });
              await finalizarJornada(loc.coords.latitude, loc.coords.longitude, jornada.km_total);
              await stopTrackingJornada();
              const novoEstado: JornadaState = { status: 'finalizada', km_total: jornada.km_total };
              setJornada(novoEstado);
              await saveJornadaState(novoEstado);

              // Gera o mapa em segundo plano sem bloquear o app
              gerarUrlMapaTrajetoria().then(async (url) => {
                await clearWaypoints();
                if (url) {
                  Alert.alert(
                    'Rota do Dia Disponivel',
                    'Deseja visualizar o mapa da sua trajetoria de hoje?',
                    [
                      { text: 'Agora Nao', style: 'cancel' },
                      { text: 'Ver Mapa', onPress: () => Linking.openURL(url) },
                    ]
                  );
                }
              }).catch(() => {});

              Alert.alert('Dia Finalizado', 'Sua jornada foi encerrada e enviada com sucesso!');
            } catch (e: any) {
              Alert.alert('Erro', e.message || 'Nao foi possivel finalizar a jornada agora.');
            }
          }
        },
      ]
    );
  };

  const realizadas = visitas.filter((v) => v.status === 'realizada').length;
  const emExecucao = visitas.filter((v) => v.checkin_time && v.status !== 'realizada').length;
  const pendentes = visitas.filter((v) => !v.checkin_time && v.status !== 'realizada').length;

  const visitasFiltradas = visitas.filter(v =>
    searchText.trim() === '' ||
    v.empresa_nome.toLowerCase().includes(searchText.toLowerCase())
  );

  const abrirNavegacao = (visita: VisitaAPI) => {
    const lat = parseFloat(visita.empresa_lat || (visita.empresa ? visita.empresa.latitude : '') || '');
    const lng = parseFloat(visita.empresa_lng || (visita.empresa ? visita.empresa.longitude : '') || '');

    if (isNaN(lat) || isNaN(lng)) {
      Alert.alert(
        'Sem coordenadas',
        `A empresa "${visita.empresa_nome}" ainda nao tem localizacao cadastrada.\n\nPeca ao administrador para detectar as coordenadas no painel web.`
      );
      return;
    }

    Alert.alert(
      'Navegar ate a Empresa',
      visita.empresa_nome,
      [
        {
          text: 'Waze',
          onPress: () =>
            Linking.openURL(`waze://?ll=${lat},${lng}&navigate=yes`).catch(() =>
              Linking.openURL(`https://waze.com/ul?ll=${lat},${lng}&navigate=yes`)
            ),
        },
        {
          text: 'Google Maps',
          onPress: () =>
            Linking.openURL(`google.navigation:q=${lat},${lng}`).catch(() =>
              Linking.openURL(`https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}`)
            ),
        },
        { text: 'Cancelar', style: 'cancel' },
      ]
    );
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container} edges={['top']}>
        <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
          <ActivityIndicator size="large" color="#3B82F6" />
          <Text style={{ color: '#94A3B8', marginTop: 12 }}>Carregando sua agenda...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        refreshControl={
          <RefreshControl
            refreshing={sincronizando}
            onRefresh={onRefresh}
            tintColor="#3B82F6"
          />
        }
      >
        {/* Banner Offline */}
        {offline && (
          <View style={styles.offlineBanner}>
            <IconSymbol name="wifi.slash" size={14} color="#FCD34D" />
            <Text style={styles.offlineText}>Modo Offline - dados do ultimo sincronismo</Text>
          </View>
        )}

        {/* Header */}
        <View style={styles.header}>
          <View style={{ flex: 1 }}>
            <Text style={styles.greeting}>Ola, {user?.first_name || user?.username || 'Consultor'}!</Text>
            <Text style={styles.dateText}>{hoje}</Text>
          </View>
          <TouchableOpacity style={styles.avatarContainer} onPress={() => setMenuVisible(true)}>
            <Image
              source={{ uri: user?.foto ? (user.foto.startsWith('http') ? user.foto : `${API_BASE_URL}${user.foto}`) : `https://ui-avatars.com/api/?name=${user?.first_name || 'C'}&background=3B82F6&color=fff` }}
              style={styles.avatar}
            />
          </TouchableOpacity>
        </View>

        {/* Banner de Jornada */}
        <View style={styles.jornadaContainer}>
          <View style={styles.jornadaInfo}>
            <Text style={styles.jornadaLabel}>JORNADA DIARIA</Text>
            {jornada.status === 'em_andamento' ? (
              <Text style={styles.jornadaValue}>{jornada.km_total.toFixed(2)} <Text style={{fontSize: 14}}>km</Text></Text>
            ) : jornada.status === 'finalizada' ? (
              <Text style={[styles.jornadaValue, {color: '#34D399'}]}>{jornada.km_total.toFixed(2)} km (Finalizada)</Text>
            ) : (
              <Text style={styles.jornadaValue}>0.00 km</Text>
            )}
          </View>
          <View style={{ justifyContent: 'center' }}>
             {jornada.status === 'nao_iniciada' ? (
               <TouchableOpacity style={styles.jornadaBtnIniciar} onPress={handleIniciarJornada}>
                 <Text style={styles.jornadaBtnText}>Iniciar Dia</Text>
               </TouchableOpacity>
             ) : jornada.status === 'em_andamento' ? (
               <TouchableOpacity style={styles.jornadaBtnFinalizar} onPress={handleFinalizarJornada}>
                 <Text style={styles.jornadaBtnText}>Finalizar Dia</Text>
               </TouchableOpacity>
             ) : (
               <View style={styles.jornadaBtnDone}>
                  <Text style={[styles.jornadaBtnText, {color: '#94A3B8'}]}>Concluido</Text>
               </View>
             )}
          </View>
        </View>

        {/* Toggle Mensal / Diario */}
        <View style={styles.toggleContainer}>
          <TouchableOpacity
            style={[styles.toggleBtn, filterMode === 'mensal' && styles.toggleBtnActive]}
            onPress={() => setFilterMode('mensal')}
          >
            <Text style={[styles.toggleText, filterMode === 'mensal' && styles.toggleTextActive]}>MENSAL</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.toggleBtn, filterMode === 'diario' && styles.toggleBtnActive]}
            onPress={() => setFilterMode('diario')}
          >
            <Text style={[styles.toggleText, filterMode === 'diario' && styles.toggleTextActive]}>DIARIO</Text>
          </TouchableOpacity>
        </View>

        {/* Cards de Resumo */}
        <View style={styles.statsContainer}>
          <View style={[styles.statCard, { backgroundColor: 'rgba(59, 130, 246, 0.15)' }]}>
            <Text style={[styles.statValue, { color: '#60A5FA' }]}>{visitas.length}</Text>
            <Text style={styles.statLabel}>Total</Text>
          </View>
          <View style={[styles.statCard, { backgroundColor: 'rgba(16, 185, 129, 0.15)' }]}>
            <Text style={[styles.statValue, { color: '#34D399' }]}>{realizadas}</Text>
            <Text style={styles.statLabel}>Feitas</Text>
          </View>
          <View style={[styles.statCard, { backgroundColor: 'rgba(56, 189, 248, 0.15)' }]}>
            <Text style={[styles.statValue, { color: '#38BDF8' }]}>{emExecucao}</Text>
            <Text style={styles.statLabel}>Em Exec.</Text>
          </View>
          <View style={[styles.statCard, { backgroundColor: 'rgba(245, 158, 11, 0.15)' }]}>
            <Text style={[styles.statValue, { color: '#FBBF24' }]}>{pendentes}</Text>
            <Text style={styles.statLabel}>Pendentes</Text>
          </View>
        </View>

        {/* Header da lista de agenda */}
        <View style={styles.listHeader}>
          <Text style={styles.listHeaderTitle}>
            {filterMode === 'mensal' ? `Mes: ${new Date(selectedDate + 'T12:00:00').toLocaleDateString('pt-BR', { month: 'long', year: 'numeric' })}` : (isHoje ? 'Sua Agenda Hoje' : `Agenda de ${new Date(selectedDate + 'T12:00:00').toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' })}`)}
          </Text>
          <View style={styles.listHeaderActions}>
            {(!user?.permissoes_mobile || user.permissoes_mobile.pode_agendar) && (
              <TouchableOpacity
                style={styles.toolbarBtn}
                onPress={() => router.push('/novo-agendamento')}
              >
                <IconSymbol name="plus" size={18} color="#FFF" />
              </TouchableOpacity>
            )}

            <TouchableOpacity
              style={styles.toolbarBtn}
              onPress={() => router.push('/pesquisa')}
            >
              <IconSymbol name="magnifyingglass" size={18} color="#94A3B8" />
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.toolbarBtn, showCalendar && styles.toolbarBtnActive]}
              onPress={() => setShowCalendar(true)}
            >
              <IconSymbol name="calendar" size={18} color={!isHoje ? '#3B82F6' : '#94A3B8'} />
              {!isHoje && <View style={styles.calendarDot} />}
            </TouchableOpacity>
          </View>
        </View>

        {visitasFiltradas.length === 0 && (
          <View style={{ alignItems: 'center', padding: 32 }}>
            <Text style={{ color: '#94A3B8', textAlign: 'center' }}>
              {searchText ? `Nenhuma empresa encontrada para "${searchText}"` : 'Nenhuma visita encontrada para esta data.'}
            </Text>
          </View>
        )}

        {visitasFiltradas.map((visita) => (
          <TouchableOpacity
            key={visita.id}
            onPress={() => router.push(`/visita/${visita.id}` as any)}
            style={[
              styles.visitaCard,
              visita.status === 'realizada' && styles.visitaCardConcluida,
              visita.checkin_time && visita.status !== 'realizada' && styles.visitaCardExecucao
            ]}
          >
            <View style={styles.visitaInfo}>
              <Text style={styles.visitaTime}>{visita.horario.substring(0, 5)}</Text>
              <View style={{ flex: 1, marginRight: 8 }}>
                <Text style={styles.visitaSchool} numberOfLines={2}>
                  {visita.empresa_nome}
                </Text>
                <Text style={[styles.visitaStatusText, visita.checkin_time && visita.status !== 'realizada' && { color: '#38BDF8' }]}>
                  {visita.status === 'realizada'
                    ? 'Finalizada'
                    : visita.checkin_time
                      ? 'Em Execucao'
                      : 'Pendente'}
                </Text>
              </View>

              {/* Botao de Navegacao */}
              <TouchableOpacity
                style={[
                  styles.navButton,
                  !(visita.empresa_lat || (visita.empresa && visita.empresa.latitude)) && styles.navButtonDisabled,
                  { marginRight: 8 }
                ]}
                onPress={(e) => { e.stopPropagation(); abrirNavegacao(visita); }}
                activeOpacity={0.7}
                hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
              >
                <Text style={styles.navButtonIcon}>Ir</Text>
              </TouchableOpacity>
              
            </View>
            <View style={[
              styles.statusCircle,
              visita.status === 'realizada'
                ? styles.statusCircleGreen
                : visita.checkin_time
                  ? styles.statusCircleBlue
                  : styles.statusCircleYellow
            ]}>
              {visita.status === 'realizada' ? (
                <IconSymbol name="checkmark" size={14} color="#059669" />
              ) : visita.checkin_time ? (
                <IconSymbol name="play.fill" size={14} color="#0284C7" />
              ) : null}
            </View>
          </TouchableOpacity>
        ))}


        {/* Modal Calendario */}
        <Modal
          visible={showCalendar}
          transparent
          animationType="slide"
          onRequestClose={() => setShowCalendar(false)}
        >
          <Pressable style={styles.calendarOverlay} onPress={() => setShowCalendar(false)}>
            <Pressable style={styles.calendarModal} onPress={e => e.stopPropagation()}>
              <View style={styles.calendarHeaderRow}>
                <Text style={styles.calendarTitle}>Selecionar Data</Text>
                <TouchableOpacity onPress={() => setShowCalendar(false)}>
                  <IconSymbol name="xmark.circle.fill" size={24} color="#475569" />
                </TouchableOpacity>
              </View>
              <Calendar
                current={selectedDate}
                onDayPress={(day: any) => {
                  setSelectedDate(day.dateString);
                  setShowCalendar(false);
                }}
                markedDates={{
                  ...markedDates,
                  [selectedDate]: { selected: true, selectedColor: '#3B82F6' }
                }}
                theme={{
                  backgroundColor: '#1E293B',
                  calendarBackground: '#1E293B',
                  textSectionTitleColor: '#64748B',
                  selectedDayBackgroundColor: '#3B82F6',
                  selectedDayTextColor: '#FFF',
                  todayTextColor: '#3B82F6',
                  dayTextColor: '#F8FAFC',
                  textDisabledColor: '#334155',
                  arrowColor: '#94A3B8',
                  monthTextColor: '#F8FAFC',
                  dotColor: '#3B82F6',
                  selectedDotColor: '#FFF',
                }}
              />
              {!isHoje && (
                <TouchableOpacity
                  style={styles.voltarHojeBtn}
                  onPress={() => { setSelectedDate(hojeISO); setShowCalendar(false); }}
                >
                  <Text style={styles.voltarHojeText}>Voltar para Hoje</Text>
                </TouchableOpacity>
              )}
            </Pressable>
          </Pressable>
        </Modal>

        {/* Menu do Avatar (Modal) */}
        <Modal
          visible={menuVisible}
          transparent={true}
          animationType="fade"
          onRequestClose={() => setMenuVisible(false)}
        >
          <Pressable style={styles.modalOverlay} onPress={() => setMenuVisible(false)}>
            <View style={styles.menuContainer}>
              <TouchableOpacity
                style={styles.menuItem}
                onPress={() => { setMenuVisible(false); router.push('/perfil'); }}
              >
                <IconSymbol name="person.fill" size={20} color="#E2E8F0" />
                <Text style={styles.menuText}>Meu Perfil</Text>
              </TouchableOpacity>

              <View style={styles.menuDivider} />

              <TouchableOpacity
                style={styles.menuItem}
                onPress={() => { setMenuVisible(false); router.push('/configuracoes'); }}
              >
                <IconSymbol name="gearshape.fill" size={20} color="#E2E8F0" />
                <Text style={styles.menuText}>Configuracoes</Text>
              </TouchableOpacity>

              <View style={styles.menuDivider} />

              <TouchableOpacity style={styles.menuItem} onPress={handleLogout}>
                <IconSymbol name="rectangle.portrait.and.arrow.right" size={20} color="#F43F5E" />
                <Text style={[styles.menuText, { color: '#F43F5E' }]}>Sair</Text>
              </TouchableOpacity>
            </View>
          </Pressable>
        </Modal>

      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0F172A',
  },
  scrollContent: {
    padding: 24,
    paddingBottom: 100,
  },
  offlineBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: 'rgba(251, 191, 36, 0.15)',
    borderWidth: 1,
    borderColor: 'rgba(251, 191, 36, 0.3)',
    borderRadius: 12,
    paddingHorizontal: 12,
    paddingVertical: 8,
    marginBottom: 20,
  },
  offlineText: {
    color: '#FCD34D',
    fontSize: 13,
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 32,
  },
  greeting: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#F8FAFC',
  },
  dateText: {
    fontSize: 14,
    color: '#94A3B8',
    marginTop: 4,
  },
  jornadaContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    backgroundColor: '#1E293B',
    borderRadius: 14,
    padding: 16,
    marginBottom: 24,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.06)',
    alignItems: 'center',
  },
  jornadaInfo: {
    flex: 1,
  },
  jornadaLabel: {
    color: '#94A3B8',
    fontSize: 12,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  jornadaValue: {
    color: '#F8FAFC',
    fontSize: 26,
    fontWeight: 'bold',
  },
  jornadaBtnIniciar: {
    backgroundColor: '#3B82F6',
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 8,
  },
  jornadaBtnFinalizar: {
    backgroundColor: '#EF4444',
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 8,
  },
  jornadaBtnDone: {
    backgroundColor: 'transparent',
    borderWidth: 1,
    borderColor: '#334155',
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 8,
  },
  jornadaBtnText: {
    color: '#FFF',
    fontWeight: 'bold',
    fontSize: 14,
  },
  avatarContainer: {
    padding: 2,
    backgroundColor: '#1E293B',
    borderRadius: 99,
  },
  avatar: {
    width: 48,
    height: 48,
    borderRadius: 24,
  },
  statsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 32,
    gap: 8,
  },
  statCard: {
    flex: 1,
    paddingVertical: 16,
    borderRadius: 16,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.05)',
  },
  statValue: {
    fontSize: 22,
    fontWeight: 'bold',
  },
  statLabel: {
    fontSize: 11,
    color: '#94A3B8',
    marginTop: 4,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#F8FAFC',
    marginBottom: 16,
  },
  visitaCard: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: 'rgba(30, 41, 59, 0.8)',
    padding: 16,
    borderRadius: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.05)',
  },
  visitaCardConcluida: {
    opacity: 0.6,
  },
  visitaCardExecucao: {
    borderColor: 'rgba(56, 189, 248, 0.4)',
    borderLeftWidth: 4,
  },
  visitaInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 16,
    flex: 1,
  },
  visitaTime: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#3B82F6',
  },
  visitaSchool: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#F8FAFC',
    marginBottom: 4,
  },
  visitaStatusText: {
    fontSize: 13,
    color: '#94A3B8',
  },
  navButton: {
    backgroundColor: '#1d4ed8', borderRadius: 10,
    paddingHorizontal: 10, paddingVertical: 6,
  },
  navButtonDisabled: { backgroundColor: '#334155' },
  navButtonIcon: { fontSize: 16 },
  statusCircle: {
    width: 24,
    height: 24,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
  },
  statusCircleGreen: {
    backgroundColor: '#D1FAE5',
  },
  statusCircleBlue: {
    backgroundColor: '#E0F2FE',
    borderWidth: 2,
    borderColor: '#38BDF8',
  },
  statusCircleYellow: {
    backgroundColor: '#FEF3C7',
    borderWidth: 2,
    borderColor: '#F59E0B',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-start',
    alignItems: 'flex-end',
  },
  menuContainer: {
    backgroundColor: '#1E293B',
    borderRadius: 12,
    paddingVertical: 8,
    width: 200,
    marginTop: 70,
    marginRight: 20,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.1)',
    elevation: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.4,
    shadowRadius: 10,
  },
  menuItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 16,
    gap: 12,
  },
  menuText: {
    color: '#E2E8F0',
    fontSize: 16,
    fontWeight: '500',
  },
  menuDivider: {
    height: 1,
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
  },
  // Header da lista com ferramentas inline
  listHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  listHeaderTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#F8FAFC',
    flex: 1,
  },
  listHeaderActions: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  dateChipSmall: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: 'rgba(59,130,246,0.15)',
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: 'rgba(59,130,246,0.3)',
  },
  toolbarBtn: {
    width: 36,
    height: 36,
    borderRadius: 10,
    backgroundColor: '#1E293B',
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.06)',
    position: 'relative',
  },
  toolbarBtnActive: {
    backgroundColor: '#3B82F6',
    borderColor: '#3B82F6',
  },
  calendarDot: {
    position: 'absolute',
    top: 4,
    right: 4,
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#F43F5E',
  },
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    backgroundColor: '#1E293B',
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 12,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.06)',
  },
  toggleContainer: {
    flexDirection: 'row',
    backgroundColor: '#1E293B',
    borderRadius: 8,
    padding: 4,
    marginBottom: 20,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.05)',
  },
  toggleBtn: {
    flex: 1,
    paddingVertical: 10,
    alignItems: 'center',
    borderRadius: 6,
  },
  toggleBtnActive: {
    backgroundColor: '#3B82F6',
  },
  toggleText: {
    color: '#94A3B8',
    fontSize: 13,
    fontWeight: 'bold',
  },
  toggleTextActive: {
    color: '#FFF',
  },
  searchInput: {
    flex: 1,
    color: '#F8FAFC',
    fontSize: 15,
    padding: 0,
  },
  // Modal Calendario
  calendarOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.6)',
    justifyContent: 'flex-end',
  },
  calendarModal: {
    backgroundColor: '#1E293B',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    paddingBottom: 30,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.08)',
  },
  calendarHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255,255,255,0.06)',
  },
  calendarTitle: {
    fontSize: 17,
    fontWeight: 'bold',
    color: '#F8FAFC',
  },
  voltarHojeBtn: {
    marginHorizontal: 20,
    marginTop: 12,
    backgroundColor: 'rgba(59,130,246,0.15)',
    borderRadius: 12,
    padding: 14,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: 'rgba(59,130,246,0.3)',
  },
  voltarHojeText: {
    color: '#60A5FA',
    fontWeight: '600',
    fontSize: 15,
  },
});
