import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, TextInput, Alert, ActivityIndicator, KeyboardAvoidingView, Platform, ScrollView } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { criarEmpresa, fetchPerfil } from '@/services/api';
import { IconSymbol } from '@/components/ui/icon-symbol';
import { useQuery } from '@tanstack/react-query';

export default function NovaEmpresaScreen() {
  const router = useRouter();
  const { data: user, isLoading: loadingPerfil } = useQuery({
    queryKey: ['userPerfil'],
    queryFn: fetchPerfil,
  });
  const [nome, setNome] = useState('');
  const [telefone, setTelefone] = useState('');
  const [email, setEmail] = useState('');
  const [salvando, setSalvando] = useState(false);

  const semPermissao = !loadingPerfil && !user?.permissoes_mobile?.pode_cadastrar_empresa;

  useEffect(() => {
    if (!semPermissao) return;
    Alert.alert('Acesso negado', 'Você não tem permissão para cadastrar empresas no aplicativo.', [
      { text: 'OK', onPress: () => router.back() }
    ]);
  }, [semPermissao, router]);

  const handleSalvar = async () => {
    if (!nome.trim()) {
      Alert.alert('Campo obrigatório', 'Informe o nome da empresa.');
      return;
    }

    try {
      setSalvando(true);
      await criarEmpresa(nome.trim(), telefone.trim() || undefined, email.trim() || undefined);
      Alert.alert('Sucesso', 'Empresa cadastrada com sucesso.', [
        { text: 'OK', onPress: () => router.back() }
      ]);
    } catch (e: any) {
      Alert.alert('Erro', e.message || 'Não foi possível cadastrar a empresa.');
    } finally {
      setSalvando(false);
    }
  };

  if (loadingPerfil) {
    return (
      <SafeAreaView style={styles.container} edges={['top']}>
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
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined} style={{ flex: 1 }}>
        <ScrollView contentContainerStyle={styles.content}>
          <View style={styles.header}>
            <TouchableOpacity style={styles.backBtn} onPress={() => router.back()}>
              <IconSymbol name="chevron.left" size={18} color="#E2E8F0" />
            </TouchableOpacity>
            <Text style={styles.title}>Nova Empresa</Text>
          </View>

          <View style={styles.formCard}>
            <Text style={styles.label}>Nome da empresa *</Text>
            <TextInput
              value={nome}
              onChangeText={setNome}
              placeholder="Ex: Escola Exemplo"
              placeholderTextColor="#64748B"
              style={styles.input}
            />

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
              placeholder="contato@empresa.com"
              placeholderTextColor="#64748B"
              keyboardType="email-address"
              autoCapitalize="none"
              style={styles.input}
            />
          </View>

          <TouchableOpacity style={[styles.saveButton, salvando && styles.disabled]} onPress={handleSalvar} disabled={salvando}>
            {salvando ? <ActivityIndicator color="#FFF" /> : <Text style={styles.saveButtonText}>Cadastrar Empresa</Text>}
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
  saveButton: {
    marginTop: 20,
    backgroundColor: '#3B82F6',
    borderRadius: 12,
    height: 50,
    justifyContent: 'center',
    alignItems: 'center',
  },
  saveButtonText: { color: '#FFF', fontSize: 16, fontWeight: 'bold' },
  disabled: { opacity: 0.7 },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
});
