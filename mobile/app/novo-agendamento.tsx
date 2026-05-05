import React, { useEffect, useState } from 'react';
import { StyleSheet, Text, View, TouchableOpacity, Alert, ActivityIndicator, ScrollView, TextInput, KeyboardAvoidingView, Platform } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter, Stack } from 'expo-router';
import { Calendar } from 'react-native-calendars';
import { useQuery } from '@tanstack/react-query';
import { IconSymbol } from '@/components/ui/icon-symbol';
import { EmpresaAPI, fetchEmpresasGlobais, criarAgendamento, fetchPerfil } from '@/services/api';

export default function NovoAgendamentoScreen() {
  const router = useRouter();
  const { data: user, isLoading: loadingPerfil } = useQuery({
    queryKey: ['userPerfil'],
    queryFn: fetchPerfil,
  });
  const [selectedDate, setSelectedDate] = useState<string>('');
  const [empresa, setEmpresa] = useState('');
  const [empresaId, setEmpresaId] = useState<number | null>(null);
  const [horario, setHorario] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [empresasGlobais, setEmpresasGlobais] = useState<EmpresaAPI[]>([]);
  const [filteredEmpresas, setFilteredEmpresas] = useState<EmpresaAPI[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);

  const semPermissao = !loadingPerfil && !user?.permissoes_mobile?.pode_agendar;

  useEffect(() => {
    if (!semPermissao) return;
    Alert.alert('Acesso negado', 'Você não tem permissão para criar agendamentos no aplicativo.', [
      { text: 'OK', onPress: () => router.back() }
    ]);
  }, [semPermissao, router]);

  useEffect(() => {
    fetchEmpresasGlobais().then(setEmpresasGlobais).catch(console.log);
  }, []);

  const handleEmpresaChange = (text: string) => {
    setEmpresa(text);
    setEmpresaId(null);
    if (text.length > 1) {
      const filtered = empresasGlobais.filter(e => e.nome.toLowerCase().includes(text.toLowerCase()));
      setFilteredEmpresas(filtered.slice(0, 6));
      setShowSuggestions(true);
    } else {
      setShowSuggestions(false);
    }
  };

  const handleSelectEmpresa = (id: number, nome: string) => {
    setEmpresa(nome);
    setEmpresaId(id);
    setShowSuggestions(false);
  };

  const handleDayPress = (day: any) => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const selected = new Date(day.dateString + 'T12:00:00');

    if (selected < today) {
      Alert.alert('Data inválida', 'Não é possível agendar para uma data que já passou.');
      return;
    }

    setSelectedDate(day.dateString);
  };

  const handleCreate = async () => {
    if (!selectedDate) {
      Alert.alert('Atenção', 'Selecione a data no calendário antes de prosseguir.');
      return;
    }
    if (!empresaId) {
      Alert.alert('Atenção', 'Selecione uma empresa válida na lista de sugestões.');
      return;
    }
    if (!horario || horario.length < 5) {
      Alert.alert('Atenção', 'Digite um horário válido (HH:MM).');
      return;
    }

    const now = new Date();
    const [year, month, day] = selectedDate.split('-');
    const [hours, minutes] = horario.split(':');
    const selectedDateTime = new Date(Number(year), Number(month) - 1, Number(day), Number(hours), Number(minutes));

    if (selectedDateTime < now) {
      Alert.alert('Data/Horário inválido', 'Não é possível agendar para um horário que já passou.');
      return;
    }

    setLoading(true);
    try {
      await criarAgendamento(empresaId, selectedDate, horario);
      Alert.alert('Sucesso', 'Agendamento criado com sucesso.', [
        { text: 'OK', onPress: () => router.back() }
      ]);
    } catch (err: any) {
      Alert.alert('Erro', err.message || 'Falha ao criar agendamento.');
    } finally {
      setLoading(false);
    }
  };

  if (loadingPerfil) {
    return (
      <SafeAreaView style={styles.container} edges={['top']}>
        <Stack.Screen options={{ headerShown: false }} />
        <View style={styles.center}>
          <ActivityIndicator size="large" color="#3B82F6" />
        </View>
      </SafeAreaView>
    );
  }

  if (semPermissao) {
    return null;
  }

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <Stack.Screen options={{ headerShown: false }} />
      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        <View style={styles.header}>
          <TouchableOpacity onPress={() => router.back()} style={styles.backBtn}>
            <IconSymbol name="chevron.left" size={20} color="#94A3B8" />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>Novo Agendamento</Text>
        </View>

        <ScrollView
          contentContainerStyle={styles.content}
          automaticallyAdjustKeyboardInsets={true}
          keyboardShouldPersistTaps="handled"
        >
          <Text style={styles.infoText}>
            Selecione a data e o horário desejados. O agendamento deve ser para uma data e horário futuros.
          </Text>

          <View style={styles.calendarWrapper}>
            <Calendar
              onDayPress={handleDayPress}
              markedDates={{
                [selectedDate]: { selected: true, selectedColor: '#3B82F6' }
              }}
              theme={{
                calendarBackground: '#1E293B',
                textSectionTitleColor: '#94A3B8',
                selectedDayBackgroundColor: '#3B82F6',
                selectedDayTextColor: '#ffffff',
                todayTextColor: '#3B82F6',
                dayTextColor: '#F8FAFC',
                textDisabledColor: '#475569',
                monthTextColor: '#F8FAFC',
                arrowColor: '#3B82F6',
              }}
            />
          </View>

          {selectedDate ? (
            <View style={styles.selectedBox}>
              <IconSymbol name="calendar.badge.clock" size={20} color="#34D399" />
              <Text style={styles.selectedText}>
                Data confirmada: {selectedDate.split('-').reverse().join('/')}
              </Text>
            </View>
          ) : null}

          <View style={styles.inputContainer}>
            <Text style={styles.label}>Empresa</Text>
            <View style={{ position: 'relative', zIndex: 10 }}>
              <TextInput
                style={styles.input}
                placeholder="Nome ou código da empresa"
                placeholderTextColor="#64748B"
                value={empresa}
                onChangeText={handleEmpresaChange}
                onFocus={() => { if (empresa.length > 1) setShowSuggestions(true); }}
                onBlur={() => { setTimeout(() => setShowSuggestions(false), 200); }}
              />
              {showSuggestions && filteredEmpresas.length > 0 && (
                <View style={styles.suggestionsContainer}>
                  {filteredEmpresas.map(e => (
                    <TouchableOpacity
                      key={e.id}
                      style={styles.suggestionItem}
                      onPress={() => handleSelectEmpresa(e.id, e.nome)}
                    >
                      <Text style={styles.suggestionText} numberOfLines={1}>{e.nome}</Text>
                    </TouchableOpacity>
                  ))}
                </View>
              )}
            </View>
          </View>

          <View style={styles.inputContainer}>
            <Text style={styles.label}>Horário</Text>
            <TextInput
              style={styles.input}
              placeholder="00:00"
              placeholderTextColor="#64748B"
              keyboardType="numeric"
              maxLength={5}
              value={horario}
              onChangeText={(text) => {
                let v = text.replace(/\D/g, '');
                if (v.length >= 3) {
                  v = `${v.substring(0, 2)}:${v.substring(2, 4)}`;
                }
                setHorario(v);
              }}
            />
          </View>

          <TouchableOpacity
            style={[styles.submitBtn, loading && { opacity: 0.7 }]}
            onPress={handleCreate}
            disabled={loading}
          >
            {loading ? (
              <ActivityIndicator color="#FFF" />
            ) : (
              <Text style={styles.submitBtnText}>Confirmar Agendamento</Text>
            )}
          </TouchableOpacity>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0F172A' },
  header: { flexDirection: 'row', alignItems: 'center', padding: 20, borderBottomWidth: 1, borderBottomColor: 'rgba(255,255,255,0.05)' },
  backBtn: { paddingRight: 16 },
  headerTitle: { fontSize: 20, fontWeight: 'bold', color: '#F8FAFC' },
  content: { padding: 20, paddingBottom: 100 },
  infoText: { color: '#94A3B8', fontSize: 14, lineHeight: 22, marginBottom: 20 },
  calendarWrapper: {
    borderRadius: 16, overflow: 'hidden', borderWidth: 1, borderColor: 'rgba(255,255,255,0.06)', marginBottom: 20, backgroundColor: '#1E293B'
  },
  selectedBox: {
    flexDirection: 'row', alignItems: 'center', gap: 10,
    backgroundColor: 'rgba(16,185,129,0.1)', paddingVertical: 14, paddingHorizontal: 16,
    borderRadius: 12, marginBottom: 20, borderWidth: 1, borderColor: 'rgba(16,185,129,0.2)'
  },
  selectedText: { color: '#34D399', fontWeight: 'bold', fontSize: 15 },
  inputContainer: { marginBottom: 24 },
  label: { color: '#E2E8F0', fontSize: 14, fontWeight: '600', marginBottom: 8, marginLeft: 4 },
  input: {
    backgroundColor: '#1E293B', color: '#F8FAFC', borderRadius: 12,
    paddingHorizontal: 16, paddingVertical: 14, fontSize: 16,
    borderWidth: 1, borderColor: 'rgba(255, 255, 255, 0.05)',
  },
  suggestionsContainer: {
    position: 'absolute',
    bottom: 58,
    left: 0,
    right: 0,
    backgroundColor: '#0F172A',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: 'rgba(59, 130, 246, 0.3)',
    maxHeight: 200,
    overflow: 'hidden',
    zIndex: 100,
    elevation: 8,
  },
  suggestionItem: {
    padding: 14,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255, 255, 255, 0.05)',
  },
  suggestionText: {
    color: '#F8FAFC',
    fontSize: 15,
  },
  submitBtn: {
    backgroundColor: '#3B82F6', borderRadius: 12, paddingVertical: 18,
    alignItems: 'center', shadowColor: '#3B82F6', shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3, shadowRadius: 8, elevation: 5,
  },
  submitBtnText: { color: '#FFF', fontSize: 16, fontWeight: 'bold' },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
});
