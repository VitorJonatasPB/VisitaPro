import React, { useState, useEffect } from 'react';
import {
  StyleSheet,
  Text,
  View,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  TextInput,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter, Stack } from 'expo-router';
import { IconSymbol } from '@/components/ui/icon-symbol';
import { VisitaAPI, fetchVisitasMes } from '@/services/api';

type FilterType = 'todos' | 'execucao' | 'pendentes' | 'concluidas';

export default function PesquisaScreen() {
  const router = useRouter();
  const [visitas, setVisitas] = useState<VisitaAPI[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchText, setSearchText] = useState('');
  const [activeFilter, setActiveFilter] = useState<FilterType>('todos');
  const [periodoMode, setPeriodoMode] = useState<'atual' | 'custom'>('atual');
  const [customMonthYear, setCustomMonthYear] = useState('');

  useEffect(() => {
    const loadMensal = async () => {
      setLoading(true);
      try {
        let dtAno = new Date().getFullYear();
        let dtMes = new Date().getMonth() + 1;

        if (periodoMode === 'custom' && customMonthYear.length === 7) {
          const parts = customMonthYear.split('/');
          const m = parseInt(parts[0], 10);
          const y = parseInt(parts[1], 10);
          if (m >= 1 && m <= 12 && y > 2000) {
            dtAno = y;
            dtMes = m;
          }
        }

        const data = await fetchVisitasMes(dtAno, dtMes);
        setVisitas(data);
      } catch (e) {
        console.log('Erro carregar agenda mes', e);
      } finally {
        setLoading(false);
      }
    };
    loadMensal();
  }, [periodoMode, customMonthYear]);

  const filtradas = visitas.filter((v) => {
    const textMatch =
      searchText.trim() === '' || v.empresa_nome.toLowerCase().includes(searchText.toLowerCase());
    if (!textMatch) return false;

    if (activeFilter === 'execucao') return Boolean(v.checkin_time) && v.status !== 'realizada';
    if (activeFilter === 'pendentes') return !v.checkin_time && v.status !== 'realizada';
    if (activeFilter === 'concluidas') return v.status === 'realizada';
    return true;
  });

  return (
    <SafeAreaView style={styles.container} edges={['top', 'bottom', 'left', 'right']}>
      <Stack.Screen options={{ headerShown: false }} />

      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()} style={styles.backBtn}>
          <IconSymbol name="chevron.left" size={20} color="#94A3B8" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Pesquisar Visitas</Text>
      </View>

      <View style={styles.searchSection}>
        <View style={styles.periodRow}>
          <TouchableOpacity
            style={[styles.periodBtn, periodoMode === 'atual' && styles.periodBtnActive]}
            onPress={() => setPeriodoMode('atual')}
          >
            <Text
              style={[styles.periodBtnText, periodoMode === 'atual' && styles.periodBtnTextActive]}
            >
              Mês Atual
            </Text>
          </TouchableOpacity>

          <View style={[styles.customPeriodInput, periodoMode === 'custom' && { borderColor: '#3B82F6' }]}>
            <TextInput
              style={styles.customPeriodTextInput}
              placeholder="Ex: 05/2026"
              placeholderTextColor="#64748B"
              keyboardType="numeric"
              maxLength={7}
              value={customMonthYear}
              onChangeText={(txt) => {
                let v = txt.replace(/\D/g, '');
                if (v.length > 2) v = v.substring(0, 2) + '/' + v.substring(2);
                setCustomMonthYear(v);
              }}
              onSubmitEditing={() => {
                if (customMonthYear.length === 7) setPeriodoMode('custom');
              }}
            />
            <TouchableOpacity
              onPress={() => {
                if (customMonthYear.length === 7) setPeriodoMode('custom');
              }}
              style={{ paddingHorizontal: 10 }}
            >
              <IconSymbol
                name="magnifyingglass"
                size={16}
                color={periodoMode === 'custom' ? '#3B82F6' : '#94A3B8'}
              />
            </TouchableOpacity>
          </View>
        </View>

        <View style={styles.searchContainer}>
          <IconSymbol name="magnifyingglass" size={18} color="#64748B" />
          <TextInput
            style={styles.searchInput}
            placeholder="Digite o nome da empresa..."
            placeholderTextColor="#64748B"
            value={searchText}
            onChangeText={setSearchText}
            autoFocus
          />
          {searchText.length > 0 && (
            <TouchableOpacity onPress={() => setSearchText('')}>
              <IconSymbol name="xmark.circle.fill" size={18} color="#64748B" />
            </TouchableOpacity>
          )}
        </View>

        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.chipScroll}>
          <View style={styles.chipRow}>
            <TouchableOpacity
              style={[styles.chip, activeFilter === 'todos' && styles.chipActive]}
              onPress={() => setActiveFilter('todos')}
            >
              <Text style={[styles.chipText, activeFilter === 'todos' && styles.chipTextActive]}>
                Todas
              </Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.chip, activeFilter === 'execucao' && styles.chipActive]}
              onPress={() => setActiveFilter('execucao')}
            >
              <View style={[styles.dot, { backgroundColor: '#38BDF8' }]} />
              <Text style={[styles.chipText, activeFilter === 'execucao' && styles.chipTextActive]}>
                Em Execução
              </Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.chip, activeFilter === 'pendentes' && styles.chipActive]}
              onPress={() => setActiveFilter('pendentes')}
            >
              <View style={[styles.dot, { backgroundColor: '#FBBF24' }]} />
              <Text style={[styles.chipText, activeFilter === 'pendentes' && styles.chipTextActive]}>
                Pendentes
              </Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.chip, activeFilter === 'concluidas' && styles.chipActive]}
              onPress={() => setActiveFilter('concluidas')}
            >
              <View style={[styles.dot, { backgroundColor: '#34D399' }]} />
              <Text style={[styles.chipText, activeFilter === 'concluidas' && styles.chipTextActive]}>
                Concluídas
              </Text>
            </TouchableOpacity>
          </View>
        </ScrollView>
      </View>

      {loading ? (
        <View style={{ flex: 1, justifyContent: 'center' }}>
          <ActivityIndicator size="large" color="#3B82F6" />
        </View>
      ) : (
        <ScrollView contentContainerStyle={styles.listContent}>
          {filtradas.length === 0 ? (
            <Text style={styles.emptyText}>Nenhuma visita encontrada.</Text>
          ) : (
            filtradas.map((visita) => (
              <TouchableOpacity
                key={visita.id}
                onPress={() => router.push(`/visita/${visita.id}` as any)}
                style={[
                  styles.visitaCard,
                  visita.status === 'realizada' && styles.visitaCardConcluida,
                  visita.checkin_time && visita.status !== 'realizada' && styles.visitaCardExecucao,
                ]}
              >
                <View style={styles.visitaHeader}>
                  <Text style={styles.visitaNome} numberOfLines={1}>
                    {visita.empresa_nome}
                  </Text>
                  {visita.status === 'realizada' ? (
                    <View style={styles.badgeSuccess}>
                      <Text style={styles.badgeText}>Realizada</Text>
                    </View>
                  ) : visita.checkin_time ? (
                    <View style={styles.badgeWarning}>
                      <Text style={styles.badgeTextWarning}>Em Exec.</Text>
                    </View>
                  ) : (
                    <View style={styles.badgeNeutral}>
                      <Text style={styles.badgeTextNeutral}>Pendente</Text>
                    </View>
                  )}
                </View>

                <View style={styles.visitaRow}>
                  <IconSymbol name="calendar" size={14} color="#64748B" />
                  <Text style={styles.visitaData}>{visita.data.split('-').reverse().join('/')}</Text>
                  <IconSymbol name="clock" size={14} color="#64748B" />
                  <Text style={styles.visitaTime}>{visita.horario.substring(0, 5)}</Text>
                </View>
              </TouchableOpacity>
            ))
          )}
        </ScrollView>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0F172A' },
  header: { flexDirection: 'row', alignItems: 'center', padding: 20 },
  backBtn: { paddingRight: 16 },
  headerTitle: { fontSize: 20, fontWeight: 'bold', color: '#F8FAFC' },
  searchSection: { paddingHorizontal: 20 },
  periodRow: { flexDirection: 'row', gap: 10, marginBottom: 16 },
  periodBtn: {
    flex: 1,
    paddingVertical: 12,
    alignItems: 'center',
    borderRadius: 8,
    backgroundColor: '#1E293B',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.05)',
  },
  periodBtnActive: { backgroundColor: '#3B82F6', borderColor: '#3B82F6' },
  periodBtnText: { color: '#94A3B8', fontSize: 14, fontWeight: 'bold' },
  periodBtnTextActive: { color: '#FFF' },
  customPeriodInput: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1E293B',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.06)',
  },
  customPeriodTextInput: {
    flex: 1,
    color: '#FFF',
    textAlign: 'center',
    fontSize: 15,
    paddingVertical: 8,
  },
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    backgroundColor: '#1E293B',
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 12,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.06)',
  },
  searchInput: { flex: 1, color: '#F8FAFC', fontSize: 16, padding: 0 },
  chipScroll: { marginVertical: 16 },
  chipRow: { flexDirection: 'row', gap: 12 },
  chip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: '#1E293B',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.06)',
  },
  chipActive: { backgroundColor: '#3B82F6', borderColor: '#3B82F6' },
  chipText: { color: '#94A3B8', fontSize: 13, fontWeight: '600' },
  chipTextActive: { color: '#FFF' },
  dot: { width: 8, height: 8, borderRadius: 4 },
  listContent: { padding: 20 },
  emptyText: { color: '#94A3B8', textAlign: 'center', marginTop: 40 },
  visitaCard: {
    backgroundColor: '#1E293B',
    borderRadius: 16,
    padding: 18,
    marginBottom: 16,
    borderLeftWidth: 4,
    borderLeftColor: '#FBBF24',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.06)',
  },
  visitaCardConcluida: { borderLeftColor: '#10B981' },
  visitaCardExecucao: { borderLeftColor: '#38BDF8' },
  visitaHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  visitaNome: { flex: 1, color: '#F8FAFC', fontSize: 17, fontWeight: 'bold' },
  badgeSuccess: {
    backgroundColor: 'rgba(16,185,129,0.15)',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
    marginLeft: 8,
  },
  badgeText: { color: '#34D399', fontSize: 12, fontWeight: 'bold' },
  badgeWarning: {
    backgroundColor: 'rgba(56,189,248,0.15)',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
    marginLeft: 8,
  },
  badgeTextWarning: { color: '#38BDF8', fontSize: 12, fontWeight: 'bold' },
  badgeNeutral: {
    backgroundColor: '#334155',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
    marginLeft: 8,
  },
  badgeTextNeutral: { color: '#CBD5E1', fontSize: 12, fontWeight: 'bold' },
  visitaRow: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  visitaData: { color: '#94A3B8', fontSize: 14, marginRight: 8 },
  visitaTime: { color: '#94A3B8', fontSize: 14 },
});
