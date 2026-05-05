import React, { useState, useEffect, useCallback } from 'react';
import { StyleSheet, Text, View, TextInput, TouchableOpacity, Image, ActivityIndicator, Alert, ScrollView } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import * as ImagePicker from 'expo-image-picker';
import { IconSymbol } from '@/components/ui/icon-symbol';
import { fetchPerfil, updatePerfil, uploadFotoPerfil, UserAPI, API_BASE_URL } from '@/services/api';

export default function PerfilScreen() {
  const router = useRouter();
  const [user, setUser] = useState<UserAPI | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // Campos editáveis
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [telefone, setTelefone] = useState('');

  const carregarPerfil = useCallback(async () => {
    try {
      const data = await fetchPerfil();
      setUser(data);
      setFirstName(data.first_name || '');
      setLastName(data.last_name || '');
      setTelefone(data.telefone || '');
    } catch {
      Alert.alert('Erro', 'Não foi possível carregar os dados do perfil.');
      router.back();
    } finally {
      setLoading(false);
    }
  }, [router]);

  useEffect(() => {
    carregarPerfil();
  }, [carregarPerfil]);

  const handleSalvar = async () => {
    setSaving(true);
    try {
      const response = await updatePerfil({
        first_name: firstName,
        last_name: lastName,
        telefone: telefone,
      });
      setUser(response);
      Alert.alert('Sucesso', 'Perfil atualizado com sucesso!');
    } catch (err: any) {
      Alert.alert('Erro', err.message || 'Não foi possível salvar os dados.');
    } finally {
      setSaving(false);
    }
  };

  const escolherFoto = async () => {
    const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (status !== 'granted') {
      Alert.alert('Acesso negado', 'Precisamos de permissão para acessar suas fotos.');
      return;
    }

    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      aspect: [1, 1],
      quality: 0.8,
    });

    if (!result.canceled) {
      const uri = result.assets[0].uri;
      enviarNovaFoto(uri);
    }
  };

  const enviarNovaFoto = async (uri: string) => {
    setLoading(true);
    try {
      const filename = uri.split('/').pop() || 'foto_perfil.jpg';
      const response = await uploadFotoPerfil(uri, filename);
      setUser(response);
      Alert.alert('Sucesso', 'Sua foto foi atualizada!');
    } catch (error: any) {
      Alert.alert('Erro', error.message || 'Falha ao enviar a nova foto.');
    } finally {
      setLoading(false);
    }
  };

  if (loading && !user) {
    return (
      <SafeAreaView style={styles.container} edges={['top']}>
        <View style={styles.center}>
          <ActivityIndicator size="large" color="#3B82F6" />
        </View>
      </SafeAreaView>
    );
  }

  const fotoUri = user?.foto 
    ? (user.foto.startsWith('http') ? user.foto : `${API_BASE_URL}${user.foto}`) 
    : `https://ui-avatars.com/api/?name=${user?.first_name || 'User'}&background=3B82F6&color=fff`;

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()} style={styles.backBtn}>
          <IconSymbol name="chevron.left" size={18} color="#94A3B8" />
          <Text style={styles.backBtnText}>Voltar</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Meu Perfil</Text>
        <View style={{ width: 70 }} />
      </View>

      <ScrollView contentContainerStyle={styles.scrollContent}>
        
        {/* Foto de Perfil */}
        <View style={styles.avatarSection}>
          <View style={styles.avatarWrapper}>
            <Image source={{ uri: fotoUri }} style={styles.avatar} />
            {loading && (
              <View style={styles.avatarLoadingOverlay}>
                <ActivityIndicator color="#FFF" />
              </View>
            )}
          </View>
          <TouchableOpacity style={styles.photoEditBtn} onPress={escolherFoto} disabled={loading}>
            <IconSymbol name="camera.fill" size={16} color="#FFF" />
            <Text style={styles.photoEditBtnText}>Alterar Foto</Text>
          </TouchableOpacity>
        </View>

        {/* Informações Fixas */}
        <View style={styles.infoCard}>
          <Text style={styles.infoLabel}>Usuário</Text>
          <Text style={styles.infoValue}>{user?.username}</Text>
          
          <View style={styles.divider} />
          
          <Text style={styles.infoLabel}>E-mail</Text>
          <Text style={styles.infoValue}>{user?.email || 'Não informado'}</Text>
        </View>

        {/* Formulário de Edição */}
        <Text style={styles.sectionTitle}>Editar Informações</Text>
        
        <View style={styles.fieldContainer}>
          <Text style={styles.label}>Nome</Text>
          <TextInput
            style={styles.input}
            value={firstName}
            onChangeText={setFirstName}
            placeholder="Seu nome"
            placeholderTextColor="#6B7280"
          />
        </View>

        <View style={styles.fieldContainer}>
          <Text style={styles.label}>Sobrenome</Text>
          <TextInput
            style={styles.input}
            value={lastName}
            onChangeText={setLastName}
            placeholder="Seu sobrenome"
            placeholderTextColor="#6B7280"
          />
        </View>

        <View style={styles.fieldContainer}>
          <Text style={styles.label}>Telefone</Text>
          <TextInput
            style={styles.input}
            value={telefone}
            onChangeText={setTelefone}
            placeholder="(00) 00000-0000"
            keyboardType="phone-pad"
            placeholderTextColor="#6B7280"
          />
        </View>

        {/* Action Button */}
        <TouchableOpacity 
          style={[styles.saveBtn, saving && styles.saveBtnDisabled]} 
          onPress={handleSalvar}
          disabled={saving}
        >
          {saving ? (
            <ActivityIndicator color="#FFF" />
          ) : (
            <Text style={styles.saveBtnText}>Salvar Alterações</Text>
          )}
        </TouchableOpacity>

      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0F172A' },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  scrollContent: { padding: 20, paddingBottom: 60 },
  header: { 
    flexDirection: 'row', 
    alignItems: 'center', 
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingTop: 10,
    paddingBottom: 20,
  },
  backBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 12,
    backgroundColor: '#1E293B',
  },
  backBtnText: {
    color: '#94A3B8',
    fontSize: 15,
    fontWeight: '500',
  },
  headerTitle: { fontSize: 20, fontWeight: 'bold', color: '#F8FAFC' },
  avatarSection: { alignItems: 'center', marginBottom: 30 },
  avatarWrapper: {
    width: 120, height: 120, borderRadius: 60,
    backgroundColor: '#1E293B',
    marginBottom: 16,
    borderWidth: 3,
    borderColor: '#3B82F6',
    overflow: 'hidden',
    justifyContent: 'center',
    alignItems: 'center'
  },
  avatar: { width: '100%', height: '100%', borderRadius: 60 },
  avatarLoadingOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  photoEditBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#334155',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 20,
  },
  photoEditBtnText: { color: '#E2E8F0', fontWeight: 'bold' },
  infoCard: {
    backgroundColor: '#1E293B',
    borderRadius: 16,
    padding: 20,
    marginBottom: 30,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.05)',
  },
  infoLabel: { fontSize: 13, color: '#94A3B8', marginBottom: 4 },
  infoValue: { fontSize: 16, color: '#F8FAFC', fontWeight: '500' },
  divider: { height: 1, backgroundColor: 'rgba(255,255,255,0.1)', marginVertical: 12 },
  sectionTitle: { fontSize: 18, fontWeight: 'bold', color: '#F8FAFC', marginBottom: 16 },
  fieldContainer: { marginBottom: 20 },
  label: { color: '#CBD5E1', fontSize: 14, fontWeight: '600', marginBottom: 8 },
  input: {
    backgroundColor: '#1E293B', color: '#F8FAFC', borderRadius: 12,
    padding: 16, fontSize: 16,
    borderWidth: 1, borderColor: 'rgba(255,255,255,0.06)',
  },
  saveBtn: {
    backgroundColor: '#3B82F6',
    padding: 18,
    borderRadius: 14,
    alignItems: 'center',
    marginTop: 10,
    elevation: 3,
    shadowColor: '#3B82F6',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
  },
  saveBtnDisabled: { opacity: 0.6 },
  saveBtnText: { color: '#FFF', fontWeight: 'bold', fontSize: 17 },
});
