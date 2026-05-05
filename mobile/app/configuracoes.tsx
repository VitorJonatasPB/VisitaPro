import React, { useState, useEffect } from 'react';
import {
  StyleSheet,
  Text,
  View,
  Switch,
  TouchableOpacity,
  ScrollView,
  Alert,
  TextInput,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import * as Location from 'expo-location';
import * as ImagePicker from 'expo-image-picker';
import { IconSymbol } from '@/components/ui/icon-symbol';
import { reportBug } from '@/services/api';

export default function ConfiguracoesScreen() {
  const router = useRouter();

  const [temaEscuro, setTemaEscuro] = useState(true);
  const [fonteGrade, setFonteGrande] = useState(false);
  const [gpsAuth, setGpsAuth] = useState(false);
  const [cameraAuth, setCameraAuth] = useState(false);
  const [bugTexto, setBugTexto] = useState('');
  const [enviandoBug, setEnviandoBug] = useState(false);

  useEffect(() => {
    verificarPermissoes();
  }, []);

  const verificarPermissoes = async () => {
    const locStatus = await Location.getForegroundPermissionsAsync();
    setGpsAuth(locStatus.status === 'granted');

    const camStatus = await ImagePicker.getMediaLibraryPermissionsAsync();
    setCameraAuth(camStatus.status === 'granted');
  };

  const handleEnviarErro = async () => {
    if (!bugTexto.trim()) {
      Alert.alert('Atenção', 'Descreva o problema antes de enviar.');
      return;
    }
    setEnviandoBug(true);
    try {
      await reportBug({ descricao: bugTexto, device_info: 'Expo Go / Mobile App' });
      Alert.alert('Sucesso', 'Obrigado! Seu erro foi repassado à equipe de suporte.');
      setBugTexto('');
    } catch (e: any) {
      Alert.alert('Erro', e.message || 'Houve uma falha ao enviar o reporte.');
    } finally {
      setEnviandoBug(false);
    }
  };

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()} style={styles.backBtn}>
          <IconSymbol name="chevron.left" size={18} color="#94A3B8" />
          <Text style={styles.backBtnText}>Voltar</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Configurações</Text>
        <View style={{ width: 70 }} />
      </View>

      <ScrollView contentContainerStyle={styles.content}>
        <Text style={styles.sectionTitle}>Aparência</Text>
        <View style={styles.card}>
          <View style={styles.rowItem}>
            <View style={styles.rowTextWrap}>
              <IconSymbol name="moon.fill" size={20} color="#F8FAFC" />
              <Text style={styles.rowText}>Modo Escuro</Text>
            </View>
            <Switch
              value={temaEscuro}
              onValueChange={setTemaEscuro}
              trackColor={{ false: '#334155', true: '#3B82F6' }}
            />
          </View>
          <View style={styles.divider} />
          <View style={styles.rowItem}>
            <View style={styles.rowTextWrap}>
              <IconSymbol name="textformat.size" size={20} color="#F8FAFC" />
              <Text style={styles.rowText}>Fonte Grande</Text>
            </View>
            <Switch
              value={fonteGrade}
              onValueChange={setFonteGrande}
              trackColor={{ false: '#334155', true: '#3B82F6' }}
            />
          </View>
        </View>

        <Text style={styles.sectionTitle}>Permissões do App</Text>
        <View style={styles.card}>
          <View style={styles.rowItem}>
            <View style={styles.rowTextWrap}>
              <IconSymbol name="location.fill" size={20} color="#F8FAFC" />
              <Text style={styles.rowText}>Acesso ao GPS</Text>
            </View>
            <Text style={[styles.statusText, gpsAuth ? styles.statusOk : styles.statusWarn]}>
              {gpsAuth ? 'Permitido' : 'Negado'}
            </Text>
          </View>
          <View style={styles.divider} />
          <View style={styles.rowItem}>
            <View style={styles.rowTextWrap}>
              <IconSymbol name="camera.fill" size={20} color="#F8FAFC" />
              <Text style={styles.rowText}>Acesso à Galeria</Text>
            </View>
            <Text style={[styles.statusText, cameraAuth ? styles.statusOk : styles.statusWarn]}>
              {cameraAuth ? 'Permitido' : 'Negado'}
            </Text>
          </View>
        </View>

        <Text style={styles.sectionTitle}>Legal</Text>
        <View style={styles.card}>
          <TouchableOpacity
            style={styles.rowItem}
            onPress={() => Alert.alert('Termos de Uso', 'Documento em construção.')}
          >
            <Text style={styles.rowText}>Termos de Uso</Text>
            <IconSymbol name="chevron.right" size={16} color="#94A3B8" />
          </TouchableOpacity>
          <View style={styles.divider} />
          <TouchableOpacity
            style={styles.rowItem}
            onPress={() => Alert.alert('Política de Privacidade', 'Documento em construção.')}
          >
            <Text style={styles.rowText}>Política de Privacidade</Text>
            <IconSymbol name="chevron.right" size={16} color="#94A3B8" />
          </TouchableOpacity>
        </View>

        <Text style={styles.sectionTitle}>Encontrou algum erro?</Text>
        <View style={styles.card}>
          <TextInput
            style={styles.textArea}
            placeholder="Descreva o que aconteceu de errado aqui..."
            placeholderTextColor="#6B7280"
            multiline
            numberOfLines={4}
            value={bugTexto}
            onChangeText={setBugTexto}
          />
          <TouchableOpacity
            style={[styles.bugBtn, enviandoBug && { opacity: 0.6 }]}
            onPress={handleEnviarErro}
            disabled={enviandoBug}
          >
            {enviandoBug ? (
              <ActivityIndicator color="#FFF" />
            ) : (
              <Text style={styles.bugBtnText}>Reportar Problema</Text>
            )}
          </TouchableOpacity>
        </View>

        <Text style={styles.versionLabel}>VisitasPro App Versão 1.0.0</Text>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0F172A' },
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
  content: { padding: 20, paddingBottom: 60 },
  sectionTitle: {
    fontSize: 16,
    color: '#94A3B8',
    fontWeight: 'bold',
    marginBottom: 12,
    marginLeft: 4,
    marginTop: 16,
  },
  card: {
    backgroundColor: '#1E293B',
    borderRadius: 16,
    paddingHorizontal: 16,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.05)',
  },
  rowItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 16,
  },
  rowTextWrap: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  rowText: { fontSize: 16, color: '#F8FAFC', fontWeight: '500' },
  divider: { height: 1, backgroundColor: 'rgba(255,255,255,0.05)' },
  statusText: { fontSize: 14, fontWeight: 'bold' },
  statusOk: { color: '#10B981' },
  statusWarn: { color: '#F43F5E' },
  textArea: {
    backgroundColor: '#0F172A',
    borderRadius: 12,
    color: '#F8FAFC',
    padding: 12,
    minHeight: 100,
    textAlignVertical: 'top',
    fontSize: 15,
    marginTop: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.05)',
  },
  bugBtn: {
    backgroundColor: '#F43F5E',
    padding: 14,
    borderRadius: 12,
    alignItems: 'center',
    marginBottom: 16,
  },
  bugBtnText: { color: '#FFF', fontWeight: 'bold', fontSize: 15 },
  versionLabel: { textAlign: 'center', marginTop: 30, color: '#64748B', fontSize: 13 },
});
