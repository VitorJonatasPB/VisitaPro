import React, { useState } from 'react';
import { View, Text, StyleSheet, FlatList, ActivityIndicator, TouchableOpacity, TextInput } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useQuery } from '@tanstack/react-query';
import { fetchProfessoresGlobais, ProfessorAPI } from '@/services/api';
import { IconSymbol } from '@/components/ui/icon-symbol';

export default function ProfessoresScreen() {
  const { data: professores = [], isLoading: loading } = useQuery({
    queryKey: ['professoresGlobal'],
    queryFn: fetchProfessoresGlobais,
  });

  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  const toggleExpand = (id: number) => {
    setExpandedId(prev => (prev === id ? null : id));
  };

  const filteredProfessores = professores.filter(p => {
    const q = searchQuery.toLowerCase();
    return p.nome.toLowerCase().includes(q) || (p.escola_nome && p.escola_nome.toLowerCase().includes(q));
  });

  const renderProfessor = ({ item }: { item: ProfessorAPI }) => {
    const isExpanded = expandedId === item.id;

    return (
      <TouchableOpacity 
        style={styles.card}
        activeOpacity={0.7}
        onPress={() => toggleExpand(item.id)}
      >
        <View style={styles.cardHeader}>
          <IconSymbol name="person.fill" size={24} color="#10B981" />
          <View style={{ flex: 1, marginLeft: 12 }}>
            <Text style={styles.cardTitle}>{item.nome}</Text>
            {item.matricula && (
               <Text style={styles.cardSubtitle}>Matrícula: {item.matricula}</Text>
            )}
            {item.escola_nome && (
               <Text style={[styles.cardSubtitle, { marginTop: 2, fontSize: 13, color: '#64748B' }]}>{item.escola_nome}</Text>
            )}
          </View>
          <IconSymbol name={isExpanded ? 'chevron.up' : 'chevron.down'} size={20} color="#94A3B8" />
        </View>

        {isExpanded && (
          <View style={styles.detailsContainer}>
            <View style={styles.detailItem}>
              <IconSymbol name="phone.fill" size={16} color="#94A3B8" />
              <Text style={styles.detailText}>{item.telefone || 'Sem telefone cadastrado'}</Text>
            </View>
            <View style={styles.detailItem}>
              <IconSymbol name="envelope.fill" size={16} color="#94A3B8" />
              <Text style={styles.detailText}>{item.email || 'Sem e-mail cadastrado'}</Text>
            </View>
          </View>
        )}
      </TouchableOpacity>
    );
  };

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <View style={styles.header}>
        <Text style={styles.title}>Professores</Text>
        <Text style={styles.subtitle}>Relacionados às suas escolas</Text>
      </View>

      <View style={styles.searchContainer}>
        <IconSymbol name="magnifyingglass" size={20} color="#94A3B8" />
        <TextInput
          style={styles.searchInput}
          placeholder="Buscar por nome ou escola..."
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
          <ActivityIndicator size="large" color="#10B981" />
        </View>
      ) : (
        <FlatList
          data={filteredProfessores}
          keyExtractor={(item) => item.id.toString()}
          renderItem={renderProfessor}
          contentContainerStyle={styles.listContainer}
          ListEmptyComponent={
            <View style={styles.center}>
              <IconSymbol name="slash.circle" size={48} color="#475569" />
              <Text style={styles.emptyText}>Você não tem professores vinculados.</Text>
            </View>
          }
        />
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0F172A',
  },
  header: {
    padding: 24,
    paddingBottom: 16,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#FFF',
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 15,
    color: '#94A3B8',
  },
  center: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  listContainer: {
    padding: 20,
    paddingTop: 10,
    paddingBottom: 100, // Espaço da TabBar
  },
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
    borderColor: 'rgba(255, 255, 255, 0.05)',
  },
  searchInput: {
    flex: 1,
    color: '#F8FAFC',
    fontSize: 16,
    marginLeft: 10,
  },
  card: {
    backgroundColor: '#1E293B',
    borderRadius: 16,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.05)',
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#F8FAFC',
    marginBottom: 2,
  },
  cardSubtitle: {
    fontSize: 14,
    color: '#94A3B8',
  },
  detailsContainer: {
    marginTop: 16,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: 'rgba(255,255,255,0.05)',
    gap: 12,
  },
  detailItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  detailText: {
    fontSize: 14,
    color: '#CBD5E1',
  },
  emptyText: {
    marginTop: 16,
    color: '#94A3B8',
    fontSize: 16,
    textAlign: 'center',
  },
});
