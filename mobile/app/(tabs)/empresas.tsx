import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  ActivityIndicator,
  TouchableOpacity,
  TextInput,
  Alert,
  Linking,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useQuery } from '@tanstack/react-query';
import { fetchEmpresasGlobais, EmpresaAPI, fetchPerfil } from '@/services/api';
import { IconSymbol } from '@/components/ui/icon-symbol';
import { useFocusEffect, useRouter } from 'expo-router';
import { useCallback } from 'react';

export default function EmpresasScreen() {
  const { data: empresas = [], isLoading: loading, refetch: refetchEmpresas } = useQuery({
    queryKey: ['empresasGlobal'],
    queryFn: fetchEmpresasGlobais,
  });

  const { data: user, refetch: refetchPerfil } = useQuery({
    queryKey: ['userPerfil'],
    queryFn: fetchPerfil,
  });

  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const router = useRouter();

  useFocusEffect(
    useCallback(() => {
      refetchPerfil();
      refetchEmpresas();
    }, [refetchEmpresas, refetchPerfil])
  );

  const toggleExpand = (id: number) => {
    setExpandedId((prev) => (prev === id ? null : id));
  };

  const abrirNavegacao = (empresa: EmpresaAPI) => {
    const lat = parseFloat(empresa.latitude ?? '');
    const lng = parseFloat(empresa.longitude ?? '');

    if (Number.isNaN(lat) || Number.isNaN(lng)) {
      Alert.alert(
        'Sem coordenadas',
        `A empresa "${empresa.nome}" ainda não tem localização cadastrada.\n\nPeça ao administrador para detectar as coordenadas no painel web.`
      );
      return;
    }

    Alert.alert('Navegar até a empresa', empresa.nome, [
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
            Linking.openURL(
              `https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}`
            )
          ),
      },
      { text: 'Cancelar', style: 'cancel' },
    ]);
  };

  const filteredEmpresas = empresas.filter((empresa) => {
    const query = searchQuery.trim().toLowerCase();
    const nome = empresa.nome.toLowerCase();
    const regiao = (empresa.regiao_nome || '').toLowerCase();
    return nome.includes(query) || regiao.includes(query);
  });

  const renderEmpresa = ({ item }: { item: EmpresaAPI }) => {
    const isExpanded = expandedId === item.id;
    const temCoordenadas = Boolean(item.latitude && item.longitude);

    return (
      <TouchableOpacity
        style={styles.card}
        activeOpacity={0.7}
        onPress={() => toggleExpand(item.id)}
      >
        <View style={styles.cardHeader}>
          <IconSymbol name="building.2.fill" size={24} color="#3B82F6" />
          <View style={styles.cardHeaderText}>
            <Text style={styles.cardTitle}>{item.nome}</Text>
            <Text style={styles.cardSubtitle}>{item.regiao_nome}</Text>
          </View>

          <TouchableOpacity
            style={[styles.navButton, !temCoordenadas && styles.navButtonDisabled]}
            onPress={() => abrirNavegacao(item)}
            activeOpacity={0.7}
            hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
          >
            <Text style={styles.navButtonIcon}>Ir</Text>
          </TouchableOpacity>

          <IconSymbol
            name={isExpanded ? 'chevron.up' : 'chevron.down'}
            size={20}
            color="#94A3B8"
            style={styles.chevron}
          />
        </View>

        {isExpanded && (
          <View style={styles.detailsContainer}>
            <View style={styles.detailItem}>
              <IconSymbol name="phone.fill" size={16} color="#94A3B8" />
              <Text style={styles.detailText}>{item.telefone || 'Sem contato'}</Text>
            </View>
            <View style={styles.detailItem}>
              <IconSymbol name="envelope.fill" size={16} color="#94A3B8" />
              <Text style={styles.detailText}>{item.email || 'Sem e-mail'}</Text>
            </View>
            <View style={styles.detailItem}>
              <IconSymbol name="clock.fill" size={16} color="#94A3B8" />
              <Text style={styles.detailText}>
                {item.ultima_visita
                  ? `Última visita: ${new Date(item.ultima_visita).toLocaleDateString('pt-BR')}`
                  : 'Nunca visitada'}
              </Text>
            </View>
          </View>
        )}
      </TouchableOpacity>
    );
  };

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <View style={styles.header}>
        <View style={styles.headerText}>
          <Text style={styles.title}>Minhas empresas</Text>
          <Text style={styles.subtitle}>Empresas em sua responsabilidade</Text>
        </View>
        {user?.permissoes_mobile?.pode_cadastrar_empresa && (
          <TouchableOpacity
            style={styles.addButton}
            onPress={() => router.push('/nova-empresa')}
          >
            <IconSymbol name="plus" size={24} color="#FFF" />
          </TouchableOpacity>
        )}
      </View>

      <View style={styles.searchContainer}>
        <IconSymbol name="magnifyingglass" size={20} color="#94A3B8" />
        <TextInput
          style={styles.searchInput}
          placeholder="Buscar por nome ou região..."
          placeholderTextColor="#64748B"
          value={searchQuery}
          onChangeText={setSearchQuery}
        />
        {searchQuery.length > 0 && (
          <TouchableOpacity onPress={() => setSearchQuery('')}>
            <IconSymbol name="xmark.circle.fill" size={20} color="#94A3B8" />
          </TouchableOpacity>
        )}
      </View>

      {loading ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color="#3B82F6" />
        </View>
      ) : (
        <FlatList
          data={filteredEmpresas}
          keyExtractor={(item) => item.id.toString()}
          renderItem={renderEmpresa}
          contentContainerStyle={styles.listContainer}
          ListEmptyComponent={
            <View style={styles.center}>
              <IconSymbol name="slash.circle" size={48} color="#475569" />
              <Text style={styles.emptyText}>Você não tem empresas vinculadas.</Text>
            </View>
          }
        />
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0F172A' },
  header: {
    padding: 24,
    paddingBottom: 16,
    flexDirection: 'row',
    alignItems: 'center',
  },
  headerText: { flex: 1 },
  addButton: {
    backgroundColor: '#3B82F6',
    width: 44,
    height: 44,
    borderRadius: 22,
    justifyContent: 'center',
    alignItems: 'center',
  },
  title: { fontSize: 28, fontWeight: 'bold', color: '#FFF', marginBottom: 4 },
  subtitle: { fontSize: 15, color: '#94A3B8' },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 20 },
  listContainer: { padding: 20, paddingTop: 10, paddingBottom: 100 },
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1E293B',
    marginHorizontal: 20,
    marginBottom: 10,
    paddingHorizontal: 16,
    height: 48,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.05)',
  },
  searchInput: { flex: 1, color: '#F8FAFC', fontSize: 16, marginLeft: 10 },
  card: {
    backgroundColor: '#1E293B',
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.05)',
  },
  cardHeader: { flexDirection: 'row', alignItems: 'center' },
  cardHeaderText: { flex: 1, marginLeft: 12 },
  cardTitle: { fontSize: 18, fontWeight: 'bold', color: '#F8FAFC', marginBottom: 2 },
  cardSubtitle: { fontSize: 14, color: '#94A3B8' },
  navButton: {
    backgroundColor: '#1D4ED8',
    borderRadius: 10,
    paddingHorizontal: 10,
    paddingVertical: 6,
    marginLeft: 8,
  },
  navButtonDisabled: { backgroundColor: '#334155' },
  navButtonIcon: { fontSize: 12, color: '#FFF', fontWeight: '700' },
  chevron: { marginLeft: 8 },
  detailsContainer: {
    marginTop: 16,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: 'rgba(255,255,255,0.05)',
    gap: 12,
  },
  detailItem: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  detailText: { fontSize: 14, color: '#CBD5E1' },
  emptyText: { marginTop: 16, color: '#94A3B8', fontSize: 16, textAlign: 'center' },
});
