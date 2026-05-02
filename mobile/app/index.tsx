import React, { useState, useEffect } from 'react';
import { StyleSheet, Text, View, TextInput, TouchableOpacity, KeyboardAvoidingView, Platform, Dimensions, Alert, ActivityIndicator, BackHandler } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { useRouter, useFocusEffect } from 'expo-router';
import { login, getAccessToken } from '@/services/api';
import * as LocalAuthentication from 'expo-local-authentication';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Ionicons } from '@expo/vector-icons';

const { width } = Dimensions.get('window');

export default function LoginScreen() {
  const router = useRouter();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [checkingBiometrics, setCheckingBiometrics] = useState(true);
  const [rememberMe, setRememberMe] = useState(true);

  useFocusEffect(
    React.useCallback(() => {
      const onBackPress = () => {
        BackHandler.exitApp();
        return true;
      };
      const subscription = BackHandler.addEventListener('hardwareBackPress', onBackPress);
      return () => subscription.remove();
    }, [])
  );

  useEffect(() => {
    carregarCredenciais();
    verificarBiometria();
  }, []);

  const carregarCredenciais = async () => {
    try {
      const savedUser = await AsyncStorage.getItem('saved_username');
      const savedPass = await AsyncStorage.getItem('saved_password');
      if (savedUser && savedPass) {
        setUsername(savedUser);
        setPassword(savedPass);
        setRememberMe(true);
      } else {
        setRememberMe(false);
      }
    } catch (e) {
      console.warn('Erro ao carregar credenciais:', e);
    }
  };

  const verificarBiometria = async () => {
    try {
      const token = await getAccessToken();
      if (!token) {
        setCheckingBiometrics(false);
        return; // Sem sessão anterior, precisa logar com usuário e senha
      }

      const hasHardware = await LocalAuthentication.hasHardwareAsync();
      const isEnrolled = await LocalAuthentication.isEnrolledAsync();

      if (hasHardware && isEnrolled) {
        // Tenta autenticar
        const result = await LocalAuthentication.authenticateAsync({
          promptMessage: 'Desbloqueie o VisitasPro',
          fallbackLabel: 'Usar Senha',
          disableDeviceFallback: false,
        });

        if (result.success) {
          router.replace('/(tabs)');
        } else {
          // Se falhar ou cancelar, deixa tentar com usuário/senha normal
          setCheckingBiometrics(false);
        }
      } else {
        // Sessão existe mas sem biometria, enviamos direto!
        router.replace('/(tabs)');
      }
    } catch (e) {
      console.warn('Erro ao verificar biometria:', e);
      setCheckingBiometrics(false);
    }
  };

  const handleLogin = async () => {
    if (!username || !password) {
      Alert.alert('Atenção', 'Por favor, preencha o usuário e a senha.');
      return;
    }
    setLoading(true);
    try {
      await login(username, password);
      
      if (rememberMe) {
        await AsyncStorage.setItem('saved_username', username);
        await AsyncStorage.setItem('saved_password', password);
      } else {
        await AsyncStorage.removeItem('saved_username');
        await AsyncStorage.removeItem('saved_password');
      }

      router.replace('/(tabs)');
    } catch (error: any) {
      const msg = error.message || '';
      if (msg.includes('esgotado') || msg.includes('AbortError')) {
        Alert.alert(
          '⏱️ Tempo Esgotado',
          'O servidor não respondeu a tempo.\n\nVerifique:\n• O servidor Django está rodando com 0.0.0.0:8000?\n• O celular está no mesmo Wi-Fi do computador?\n• O IP no app está correto?'
        );
      } else if (msg.includes('conectar') || msg.includes('Network')) {
        Alert.alert(
          '🔌 Sem Conexão',
          'Não foi possível alcançar o servidor.\n\nVerifique:\n• O servidor está rodando?\n• O IP configurado no app está correto?'
        );
      } else if (msg.includes('401') || msg.includes('credenciais') || msg.includes('No active account')) {
        Alert.alert('🔐 Acesso Negado', 'Usuário ou senha incorretos.');
      } else {
        Alert.alert('❌ Erro no Login', msg || 'Falha desconhecida ao conectar.');
      }
    } finally {
      setLoading(false);
    }
  };

  if (checkingBiometrics) {
    return (
      <View style={styles.container}>
        <StatusBar style="light" />
        <ActivityIndicator size="large" color="#3B82F6" />
        <Text style={{ color: '#94A3B8', marginTop: 16 }}>Verificando segurança...</Text>
      </View>
    );
  }

  return (
    <KeyboardAvoidingView 
      style={styles.container} 
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <StatusBar style="light" />
      
      {/* Círculos de Fundo Estilizados */}
      <View style={[styles.circle, styles.circleTop]} />
      <View style={[styles.circle, styles.circleBottom]} />

      <View style={styles.formContainer}>
        <View style={styles.headerContainer}>
          <Text style={styles.title}>VisitasPro</Text>
          <Text style={styles.subtitle}>Portal do Consultor</Text>
        </View>

        <View style={styles.inputContainer}>
          <Text style={styles.label}>Nome de Usuário</Text>
          <TextInput
            style={styles.input}
            placeholder="Digite seu usuário"
            placeholderTextColor="#888"
            value={username}
            onChangeText={setUsername}
            autoCapitalize="none"
          />
        </View>

        <View style={styles.inputContainer}>
          <Text style={styles.label}>Senha</Text>
          <TextInput
            style={styles.input}
            placeholder="Digite sua senha"
            placeholderTextColor="#888"
            secureTextEntry
            value={password}
            onChangeText={setPassword}
          />
        </View>

        <View style={styles.rememberMeContainer}>
          <TouchableOpacity 
            style={styles.checkboxContainer} 
            onPress={() => setRememberMe(!rememberMe)}
            activeOpacity={0.7}
          >
            <View style={[styles.checkbox, rememberMe && styles.checkboxChecked]}>
              {rememberMe && <Ionicons name="checkmark" size={14} color="#FFF" />}
            </View>
            <Text style={styles.rememberMeText}>Lembrar-me</Text>
          </TouchableOpacity>

          <TouchableOpacity onPress={() => router.push('/recuperar-senha')}>
            <Text style={styles.forgotPasswordTextInline}>Esqueci a senha?</Text>
          </TouchableOpacity>
        </View>

        <TouchableOpacity 
          style={[styles.button, loading && { opacity: 0.7 }]} 
          onPress={handleLogin}
          disabled={loading}
        >
          {loading ? (
            <ActivityIndicator color="#FFF" />
          ) : (
            <Text style={styles.buttonText}>Entrar</Text>
          )}
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0F172A', // Slate 900 (Dark Modern)
    justifyContent: 'center',
    alignItems: 'center',
  },
  circle: {
    position: 'absolute',
    borderRadius: 999,
    opacity: 0.15,
  },
  circleTop: {
    width: width * 1.5,
    height: width * 1.5,
    backgroundColor: '#3B82F6', // Blue 500
    top: -width * 0.8,
    right: -width * 0.2,
  },
  circleBottom: {
    width: width,
    height: width,
    backgroundColor: '#8B5CF6', // Purple 500
    bottom: -width * 0.4,
    left: -width * 0.3,
  },
  formContainer: {
    width: '85%',
    maxWidth: 400,
    backgroundColor: 'rgba(30, 41, 59, 0.7)', // Slate 800 with opacity
    padding: 30,
    borderRadius: 24,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.3,
    shadowRadius: 20,
    elevation: 10,
  },
  headerContainer: {
    marginBottom: 40,
    alignItems: 'center',
  },
  title: {
    fontSize: 42,
    fontWeight: 'bold',
    color: '#FFFFFF',
    letterSpacing: 1,
  },
  subtitle: {
    fontSize: 16,
    color: '#94A3B8', // Slate 400
    marginTop: 8,
  },
  inputContainer: {
    marginBottom: 20,
  },
  label: {
    color: '#E2E8F0', // Slate 200
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 8,
    marginLeft: 4,
  },
  input: {
    backgroundColor: 'rgba(15, 23, 42, 0.6)', // Slate 900
    color: '#FFFFFF',
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 14,
    fontSize: 16,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.05)',
  },
  button: {
    backgroundColor: '#2563EB', // Blue 600
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
    marginTop: 10,
    shadowColor: '#2563EB',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.4,
    shadowRadius: 8,
    elevation: 5,
  },
  buttonText: {
    color: '#FFFFFF',
    fontSize: 18,
    fontWeight: 'bold',
    letterSpacing: 0.5,
  },
  rememberMeContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
    marginTop: -5,
  },
  checkboxContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  checkbox: {
    width: 20,
    height: 20,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
    marginRight: 8,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: 'rgba(15, 23, 42, 0.6)',
  },
  checkboxChecked: {
    backgroundColor: '#3B82F6',
    borderColor: '#3B82F6',
  },
  rememberMeText: {
    color: '#3B82F6',
    fontSize: 14,
  },
  forgotPasswordTextInline: {
    color: '#3B82F6',
    fontSize: 14,
    fontWeight: '500',
  },
});
