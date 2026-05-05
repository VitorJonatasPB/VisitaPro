import React, { useMemo, useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, TextInput, Alert, ActivityIndicator, KeyboardAvoidingView, Platform, ScrollView } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { criarFuncionario, fetchEmpresasGlobais } from '@/services/api';
import { IconSymbol } from '@/components/ui/icon-symbol';
import { useQuery } from '@tanstack/react-query';

export default function NovoFuncionarioScreen() {
  const router = useRouter();
  const { data: empresas = [] } = useQuery({
    queryKey: ['empresasGlobal'],
    queryFn: fetchEmpresasGlobais,
  });

  const [nome, setNome] = useState('');
  const [empresaId, setEmpresaId] = useState<number | null>(null);
  const [telefone, setTelefone] = useState('');
  const [email, setEmail] = useState('');
  const [cargo, setCargo] = useState('');
  const [departamento, setDepartamento] = useState('');
  const [salvando, setSalvando] = useState(false);

  const empresaSelecionadaNome = useMemo(() => {
    const empresa = empresas.find(e => e.id === empresaId);
    return empresa?.nome || 'Selecionar empresa';
  }, [empresaId, empresas]);

  const handleEscolherEmpresa = () => {
    if (empresas.length === 0) {
      Alert.alert('Sem empresas', 'Nenhuma empresa disponível para vincular.');
      return;
    }

    const proximas = empresas.slice(0, 12);
    const texto = proximas
      .map((e, idx) => `${idx + 1}. ${e.nome}`)
      .join('\n');

    Alert.alert(
      'Selecionar empresa',
      `Toque em uma opção:\n\n${texto}`,
      proximas.map(e => ({ text: e.nome, onPress: () => setEmpresaId(e.id) }))
    );
  };

  const handleSalvar = async () => {
    if (!nome.trim()) {
      Alert.alert('Campo obrigatório', 'Informe o nome do funcionário.');
      return;
    }
    if (!empresaId) {
      Alert.alert('Campo obrigatório', 'Selecione uma empresa.');
      return;
    }

    try {
      setSalvando(true);
      await criarFuncionario(
        nome.trim(),
        empresaId,
        telefone.trim() || undefined,
        email.trim() || undefined,
        departamento.trim() || undefined,
        cargo.trim() || undefined,
      );
      Alert.alert('Sucesso', 'Funcionário cadastrado com sucesso.', [
        { text: 'OK', onPress: () => router.back() }
      ]);
    } catch (e: any) {
      Alert.alert('Erro', e.message || 'Não foi possível cadastrar o funcionário.');
    } finally {
      setSalvando(false);
    }
  };

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined} style={{ flex: 1 }}>
        <ScrollView contentContainerStyle={styles.content}>
          <View style={styles.header}>
            <TouchableOpacity style={styles.backBtn} onPress={() => router.back()}>
              <IconSymbol name="chevron.left" size={18} color="#E2E8F0" />
            </TouchableOpacity>
            <Text style={styles.title}>Novo Funcionário</Text>
          </View>

          <View style={styles.formCard}>
            <Text style={styles.label}>Nome *</Text>
            <TextInput
              value={nome}
              onChangeText={setNome}
              placeholder="Ex: Maria Souza"
              placeholderTextColor="#64748B"
              style={styles.input}
            />

            <Text style={styles.label}>Empresa *</Text>
            <TouchableOpacity style={styles.selector} onPress={handleEscolherEmpresa}>
              <Text style={styles.selectorText}>{empresaSelecionadaNome}</Text>
              <IconSymbol name="chevron.down" size={16} color="#94A3B8" />
            </TouchableOpacity>

            <Text style={styles.label}>Telefone</Text>
            <TextInput
              value={telefone}
              onChangeText={setTelefone}
              placeholder="(00) 00000-0000"
              placeholderTextColor="#64748B"
              keyboardType="phone-pad"
              style={styles.input}
            />

            <Text style={styles.label}>E-mail</Text>
            <TextInput
              value={email}
              onChangeText={setEmail}
              placeholder="maria@empresa.com"
              placeholderTextColor="#64748B"
              keyboardType="email-address"
              autoCapitalize="none"
              style={styles.input}
            />

            <Text style={styles.label}>Cargo</Text>
            <TextInput
              value={cargo}
              onChangeText={setCargo}
              placeholder="Ex: Coordenadora"
              placeholderTextColor="#64748B"
              style={styles.input}
            />

            <Text style={styles.label}>Departamento</Text>
            <TextInput
              value={departamento}
              onChangeText={setDepartamento}
              placeholder="Ex: Pedagógico"
              placeholderTextColor="#64748B"
              style={styles.input}
            />
          </View>

          <TouchableOpacity style={[styles.saveButton, salvando && styles.disabled]} onPress={handleSalvar} disabled={salvando}>
            {salvando ? <ActivityIndicator color="#FFF" /> : <Text style={styles.saveButtonText}>Cadastrar Funcionário</Text>}
          </TouchableOpacity>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0F172A' },
  content: { padding: 24, paddingBottom: 40 },
  header: { flexDirection: 'row', alignItems: 'center', gap: 12, marginBottom: 24 },
  backBtn: {
    width: 36,
    height: 36,
    borderRadius: 10,
    backgroundColor: '#1E293B',
    justifyContent: 'center',
    alignItems: 'center',
  },
  title: { fontSize: 26, fontWeight: 'bold', color: '#F8FAFC' },
  formCard: {
    backgroundColor: '#1E293B',
    borderRadius: 16,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.05)',
    padding: 18,
  },
  label: { color: '#CBD5E1', fontSize: 14, marginBottom: 8, marginTop: 10 },
  input: {
    backgroundColor: '#0F172A',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.08)',
    borderRadius: 12,
    color: '#F8FAFC',
    paddingHorizontal: 12,
    paddingVertical: 12,
    fontSize: 15,
  },
  selector: {
    backgroundColor: '#0F172A',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.08)',
    borderRadius: 12,
    paddingHorizontal: 12,
    paddingVertical: 14,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  selectorText: { color: '#F8FAFC', fontSize: 15 },
  saveButton: {
    marginTop: 20,
    backgroundColor: '#10B981',
    borderRadius: 12,
    height: 50,
    justifyContent: 'center',
    alignItems: 'center',
  },
  saveButtonText: { color: '#FFF', fontSize: 16, fontWeight: 'bold' },
  disabled: { opacity: 0.7 },
});
