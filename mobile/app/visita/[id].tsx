  import React, { useState, useEffect, useCallback } from 'react';
import {
  StyleSheet, Text, View, ScrollView, TouchableOpacity,
  TextInput, ActivityIndicator, Alert, Switch, Platform, Image, Modal
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLocalSearchParams, useRouter } from 'expo-router';
import * as Location from 'expo-location';
import * as ImagePicker from 'expo-image-picker';
import { IconSymbol } from '@/components/ui/icon-symbol';
import { carregarAgendaLocal, carregarPerguntasLocal, adicionarNaFila } from '@/services/storage';
import { realizarCheckin, realizarCheckout, enviarRelatorio, VisitaAPI, PerguntaAPI, fetchFuncionariosEmpresa, FuncionarioAPI, fetchVisitaById, fetchPerguntas } from '@/services/api';
import { processarFilaDeSincronismo } from '@/services/sync';
import SignatureScreen from 'react-native-signature-canvas';
import * as DocumentPicker from 'expo-document-picker';
import * as ScreenOrientation from 'expo-screen-orientation';

export default function VisitaDetalheScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();

  const [visita, setVisita] = useState<VisitaAPI | null>(null);
  const [perguntas, setPerguntas] = useState<PerguntaAPI[]>([]);
  const [respostas, setRespostas] = useState<Record<number, string>>({});
  const [assinatura, setAssinatura] = useState<string | null>(null);
  const [showSignModal, setShowSignModal] = useState(false);

  // Fase 6: Funcionários e Fotos
  const [funcionarios, setFuncionarios] = useState<FuncionarioAPI[]>([]);
  const [funcionariosSelecionados, setFuncionariosSelecionados] = useState<number[]>([]);
  const [fotos, setFotos] = useState<string[]>([]);

  // Novo layout: Navegação interna e Docs
  const [activeMenu, setActiveMenu] = useState<'info' | 'relatorio' | 'docs' | 'ajuda'>('info');
  const [documentos, setDocumentos] = useState<{uri: string, name: string}[]>([]);

  const [loading, setLoading] = useState(true);
  const [enviando, setEnviando] = useState(false);
  const [checkinFeito, setCheckinFeito] = useState(false);

  // Geofencing
  const [showGeofenceModal, setShowGeofenceModal] = useState(false);
  const [pendingGps, setPendingGps] = useState<{ lat: number; lng: number } | null>(null);
  const [justificativa, setJustificativa] = useState('');

  const carregarDados = useCallback(async () => {
    // 1. Prioriza a API que agora possui fallback offline e Mesclagem com a Fila!
    let visitaEncontrada: VisitaAPI | undefined;
    try {
      visitaEncontrada = await fetchVisitaById(Number(id));
    } catch (e) {
      // 2. Fallback de extrema segurança pro storage local antigo
      try {
        const agenda = await carregarAgendaLocal();
        visitaEncontrada = agenda.find((v) => String(v.id) === id);
      } catch (_) {}
    }

    setVisita(visitaEncontrada || null);
    setCheckinFeito(!!visitaEncontrada?.checkin_time);

    // 3. Carregar perguntas: tenta online primeiro, faça fallback no storage
    try {
      const pergsOnline = await fetchPerguntas();
      setPerguntas(pergsOnline);
    } catch (_) {
      const pergsLocal = await carregarPerguntasLocal();
      setPerguntas(pergsLocal);
    }

    // 4. Carregar funcionários vinculados à empresa
    if (visitaEncontrada) {
      try {
        const profs = await fetchFuncionariosEmpresa(visitaEncontrada.id);
        setFuncionarios(profs);
      } catch (e) {
        console.log('Erro ao carregar funcionários da empresa:', e);
      }
    }

    setLoading(false);
  }, [id]);

  useEffect(() => {
    carregarDados();
  }, [carregarDados]);

  // Rotacionar dispositivo para horizontal ao abrir o modal de assinatura
  useEffect(() => {
    if (showSignModal) {
      ScreenOrientation.lockAsync(ScreenOrientation.OrientationLock.LANDSCAPE_RIGHT).catch(() => {});
    } else {
      ScreenOrientation.lockAsync(ScreenOrientation.OrientationLock.PORTRAIT_UP).catch(() => {});
    }
  }, [showSignModal]);

  const obterGPS = async (): Promise<{ lat: number; lng: number } | null> => {
    const { status } = await Location.requestForegroundPermissionsAsync();
    if (status !== 'granted') {
      Alert.alert('Permissão negada', 'Precisamos de acesso à localização para o Check-in.');
      return null;
    }
    const location = await Location.getCurrentPositionAsync({ accuracy: Location.Accuracy.High });
    return { lat: location.coords.latitude, lng: location.coords.longitude };
  };

  // Haversine: calcula distância em metros entre dois pontos GPS
  const haversineDistancia = (lat1: number, lng1: number, lat2: number, lng2: number): number => {
    const R = 6371000; // raio da Terra em metros
    const toRad = (v: number) => (v * Math.PI) / 180;
    const dLat = toRad(lat2 - lat1);
    const dLng = toRad(lng2 - lng1);
    const a = Math.sin(dLat / 2) ** 2 +
              Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLng / 2) ** 2;
    return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  };

  const executarCheckin = async (gps: { lat: number; lng: number }, just?: string) => {
    if (!visita) return;
    try {
      const result = await realizarCheckin(visita.id, gps.lat, gps.lng, just);
      setCheckinFeito(true);
      if (result && (result as any).offline) {
        Alert.alert('📶 Sem conexão', (result as any).message);
      } else {
        Alert.alert('✅ Check-in realizado!', 'Sua chegada foi registrada com sucesso.');
      }
    } catch {
      Alert.alert('Erro', 'Não foi possível registrar o check-in.');
    }
  };

  const handleCheckin = async () => {
    Alert.alert('Check-in', 'Confirmar chegada nesta empresa?', [
      { text: 'Cancelar', style: 'cancel' },
      {
        text: 'Confirmar', onPress: async () => {
          const gps = await obterGPS();
          if (!gps || !visita) return;

          // Verificar Geofencing
          const empresaLat = parseFloat(visita.empresa?.latitude ?? '');
          const empresaLng = parseFloat(visita.empresa?.longitude ?? '');

          if (!isNaN(empresaLat) && !isNaN(empresaLng)) {
            const dist = haversineDistancia(gps.lat, gps.lng, empresaLat, empresaLng);
            if (dist > 500) {
              // Guarda o GPS pendente e abre o modal de justificativa
              setPendingGps(gps);
              setJustificativa('');
              setShowGeofenceModal(true);
              return;
            }
          }

          await executarCheckin(gps);
        }
      }
    ]);
  };

  const handleEnviarRelatorio = async () => {
    const respostasArray = Object.entries(respostas).map(([perguntaId, resposta]) => ({
      pergunta: Number(perguntaId),
      resposta,
    }));

    if (respostasArray.length === 0) {
      Alert.alert('Atenção', 'Por favor, responda pelo menos uma pergunta antes de enviar.');
      return;
    }

    if (!assinatura) {
      Alert.alert('Atenção', 'A assinatura da visita é obrigatória.');
      return;
    }

    Alert.alert('Enviar Relatório', 'Finalizar a visita e registrar o check-out?', [
      { text: 'Cancelar', style: 'cancel' },
      {
        text: 'Finalizar', onPress: async () => {
          setEnviando(true);
          const gps = await obterGPS();
          if (!visita) return;

          try {
            let chOutResult;
            if (gps) {
              chOutResult = await realizarCheckout(visita.id, gps.lat, gps.lng);
            }
            const relResult = await enviarRelatorio(visita.id, respostasArray, assinatura, funcionariosSelecionados, fotos);
            
            if ((relResult && (relResult as any).offline) || (chOutResult && (chOutResult as any).offline)) {
               Alert.alert('📶 Salvo Offline', 'Relatório e check-out salvos. Serão enviados quando houver internet.', [
                 { text: 'OK', onPress: () => router.back() }
               ]);
            } else {
               Alert.alert('🎉 Visita concluída!', 'Relatório e check-out enviados com sucesso.', [
                 { text: 'OK', onPress: () => router.back() }
               ]);
            }
          } catch {
             Alert.alert('Erro', 'Não foi possível enviar o relatório.');
          } finally {
            setEnviando(false);
          }
        }
      }
    ]);
  };

  const renderCampoPergunta = (pergunta: PerguntaAPI) => {
    const valor = respostas[pergunta.id] || '';
    const setValor = (v: string) => setRespostas(prev => ({ ...prev, [pergunta.id]: v }));

    switch (pergunta.tipo_resposta) {
      case 'booleano':
        return (
          <View style={styles.switchRow} key={pergunta.id}>
            <Text style={styles.switchLabel}>{pergunta.texto}</Text>
            <Switch
              value={valor === 'true'}
              onValueChange={(v) => setValor(v ? 'true' : 'false')}
              trackColor={{ false: '#374151', true: '#3B82F6' }}
              thumbColor={valor === 'true' ? '#fff' : '#9CA3AF'}
            />
          </View>
        );

      case 'multipla_escolha':
        const opcoes = (pergunta.opcoes_resposta || '').split(',').map(o => o.trim());
        return (
          <View key={pergunta.id} style={styles.fieldContainer}>
            <Text style={styles.label}>{pergunta.texto}</Text>
            <View style={styles.opcoesContainer}>
              {opcoes.map((opcao) => (
                <TouchableOpacity
                  key={opcao}
                  style={[styles.opcaoBtn, valor === opcao && styles.opcaoBtnSelected]}
                  onPress={() => setValor(opcao)}
                >
                  <Text style={[styles.opcaoText, valor === opcao && styles.opcaoTextSelected]}>
                    {opcao}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>
        );

      case 'numero':
        return (
          <View key={pergunta.id} style={styles.fieldContainer}>
            <Text style={styles.label}>{pergunta.texto}</Text>
            <TextInput
              style={styles.input}
              value={valor}
              onChangeText={setValor}
              keyboardType="numeric"
              placeholder="0"
              placeholderTextColor="#6B7280"
            />
          </View>
        );

      default: // texto, texto_longo, data
        return (
          <View key={pergunta.id} style={styles.fieldContainer}>
            <Text style={styles.label}>{pergunta.texto}</Text>
            <TextInput
              style={[styles.input, pergunta.tipo_resposta === 'texto_longo' && styles.inputLong]}
              value={valor}
              onChangeText={setValor}
              multiline={pergunta.tipo_resposta === 'texto_longo'}
              keyboardType={pergunta.tipo_resposta === 'data' ? 'default' : 'default'}
              placeholder={pergunta.tipo_resposta === 'data' ? 'DD/MM/AAAA' : 'Sua resposta...'}
              placeholderTextColor="#6B7280"
            />
          </View>
        );
    }
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container} edges={['top']}>
        <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
          <ActivityIndicator size="large" color="#3B82F6" />
        </View>
      </SafeAreaView>
    );
  }

  if (!visita) {
    return (
      <SafeAreaView style={styles.container} edges={['top']}>
        <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
          <Text style={{ color: '#94A3B8' }}>Visita não encontrada.</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <ScrollView contentContainerStyle={styles.scrollContent}>

        {/* Header com Voltar */}
        <View style={styles.header}>
          <TouchableOpacity onPress={() => router.back()} style={styles.backBtn}>
            <IconSymbol name="chevron.left" size={18} color="#94A3B8" />
            <Text style={styles.backBtnText}>Voltar</Text>
          </TouchableOpacity>
          <View style={{ flex: 1 }}>
            <Text style={styles.schoolName}>{visita.empresa_nome}</Text>
            <Text style={styles.visitaDate}>{visita.data} às {visita.horario.substring(0, 5)}</Text>
          </View>
        </View>

        {/* Botões de Ação (Check-in/Check-out) */}
        {!checkinFeito ? (
          <TouchableOpacity
            style={styles.checkinBtn}
            onPress={handleCheckin}
          >
            <IconSymbol name="location.fill" size={20} color="#FFF" />
            <Text style={styles.checkinText}>Fazer Check-in (GPS)</Text>
          </TouchableOpacity>
        ) : (
          <TouchableOpacity
            style={[styles.submitBtn, enviando && styles.submitBtnDisabled]}
            onPress={handleEnviarRelatorio}
            disabled={enviando}
          >
            {enviando
              ? <ActivityIndicator color="#FFF" />
              : <>
                  <IconSymbol name="checkmark.circle" size={20} color="#FFF" />
                  <Text style={styles.submitText}>Finalizar Visita e Check-out</Text>
                </>
            }
          </TouchableOpacity>
        )}

        {/* Menu de Navegação Horizontal */}
        <View style={styles.menuContainer}>
          <TouchableOpacity style={[styles.menuBtn, activeMenu === 'info' && styles.menuBtnActive]} onPress={() => setActiveMenu('info')}>
            <IconSymbol name="info.circle" size={18} color={activeMenu === 'info' ? '#FFF' : '#94A3B8'} />
            <Text style={[styles.menuBtnText, activeMenu === 'info' && styles.menuBtnTextActive]}>Empresa</Text>
          </TouchableOpacity>
          <TouchableOpacity style={[styles.menuBtn, activeMenu === 'relatorio' && styles.menuBtnActive]} onPress={() => setActiveMenu('relatorio')}>
            <IconSymbol name="doc.text" size={18} color={activeMenu === 'relatorio' ? '#FFF' : '#94A3B8'} />
            <Text style={[styles.menuBtnText, activeMenu === 'relatorio' && styles.menuBtnTextActive]}>Relatório</Text>
          </TouchableOpacity>
          <TouchableOpacity style={[styles.menuBtn, activeMenu === 'docs' && styles.menuBtnActive]} onPress={() => setActiveMenu('docs')}>
            <IconSymbol name="folder" size={18} color={activeMenu === 'docs' ? '#FFF' : '#94A3B8'} />
            <Text style={[styles.menuBtnText, activeMenu === 'docs' && styles.menuBtnTextActive]}>Docs</Text>
          </TouchableOpacity>
          <TouchableOpacity style={[styles.menuBtn, activeMenu === 'ajuda' && styles.menuBtnActive]} onPress={() => setActiveMenu('ajuda')}>
            <IconSymbol name="questionmark.circle" size={18} color={activeMenu === 'ajuda' ? '#FFF' : '#94A3B8'} />
            <Text style={[styles.menuBtnText, activeMenu === 'ajuda' && styles.menuBtnTextActive]}>Ajuda</Text>
          </TouchableOpacity>
        </View>

        {/* ----------------- ABA INFO EMPRESA ----------------- */}
        {activeMenu === 'info' && (
          <View style={styles.tabContent}>
            <Text style={styles.sectionTitle}>🏫 Dados da Empresa</Text>
            {visita.empresa ? (
              <View style={styles.cardInfo}>
                <View style={styles.infoRow}><Text style={styles.infoLabel}>Nome:</Text><Text style={styles.infoValue}>{visita.empresa.nome}</Text></View>
                <View style={styles.infoRow}><Text style={styles.infoLabel}>CDE/Região:</Text><Text style={styles.infoValue}>{visita.empresa.regiao_nome}</Text></View>
                <View style={styles.infoRow}><Text style={styles.infoLabel}>Telefone:</Text><Text style={styles.infoValue}>{visita.empresa.telefone || 'N/A'}</Text></View>
                <View style={styles.infoRow}><Text style={styles.infoLabel}>Email:</Text><Text style={styles.infoValue}>{visita.empresa.email || 'N/A'}</Text></View>
                <View style={styles.infoRow}><Text style={styles.infoLabel}>Status:</Text><Text style={styles.infoValue}>{visita.empresa.status === 'A' ? 'Ativa' : 'Inativa'}</Text></View>
                <View style={styles.infoRow}><Text style={styles.infoLabel}>Última Visita:</Text><Text style={styles.infoValue}>{visita.empresa.ultima_visita || 'Nunca'}</Text></View>
              </View>
            ) : (
              <Text style={styles.hintText2}>Dados detalhados não sincronizados para visualização offline. Conecte-se e abra a agenda novamente.</Text>
            )}
          </View>
        )}

        {/* ----------------- ABA RELÁTORIO ----------------- */}
        {activeMenu === 'relatorio' && (
          <View style={styles.tabContent}>
            <Text style={styles.sectionTitle}>📋 Questionário e Fotos</Text>
            
            {perguntas.length === 0 && (
              <View style={styles.emptyBox}>
                <Text style={styles.emptyText}>Nenhuma pergunta disponível.</Text>
              </View>
            )}
            
            {perguntas.map(renderCampoPergunta)}

            {/* Funcionários Atendidos */}
            {funcionarios.length > 0 && (
              <View style={styles.fieldContainer}>
                <Text style={[styles.sectionTitle, { marginTop: 10, marginBottom: 8 }]}>👥 Funcionários Atendidos</Text>
                <View style={styles.opcoesContainer}>
                  {funcionarios.map((prof) => {
                    const isSelected = funcionariosSelecionados.includes(prof.id);
                    return (
                      <TouchableOpacity
                        key={prof.id}
                        style={[styles.opcaoBtn, isSelected && styles.opcaoBtnSelected]}
                        onPress={() => setFuncionariosSelecionados(prev => isSelected ? prev.filter(p => p !== prof.id) : [...prev, prof.id])}
                      >
                        <Text style={[styles.opcaoText, isSelected && styles.opcaoTextSelected]}>{prof.nome}</Text>
                      </TouchableOpacity>
                    );
                  })}
                </View>
              </View>
            )}

            {/* Fotos da Visita */}
            <Text style={[styles.sectionTitle, { marginTop: 20 }]}>📷 Fotos da Visita</Text>
            <TouchableOpacity style={styles.addPhotoBox} onPress={async () => {
              const result = await ImagePicker.launchImageLibraryAsync({ mediaTypes: ImagePicker.MediaTypeOptions.Images, allowsMultipleSelection: true, quality: 0.7, selectionLimit: 5 });
              if (!result.canceled && result.assets) setFotos(prev => [...prev, ...result.assets.map(a => a.uri)]);
            }}>
              <IconSymbol name="camera.fill" size={28} color="#94A3B8" />
              <Text style={styles.addPhotoBoxText}>Toque aqui para adicionar fotos</Text>
            </TouchableOpacity>

            {fotos.length > 0 && (
              <View style={styles.fotosContainer}>
                {fotos.map((uri, idx) => (
                  <View key={idx} style={styles.miniFotoWrapper}>
                    <Image source={{ uri }} style={styles.miniFoto} />
                    <TouchableOpacity onPress={() => setFotos(f => f.filter((_, i) => i !== idx))} style={styles.remMiniFotoBtn}><IconSymbol name="xmark" size={12} color="#FFF" /></TouchableOpacity>
                  </View>
                ))}
              </View>
            )}

            {/* Assinatura Digital */}
            <Text style={[styles.sectionTitle, { marginTop: 20 }]}>✍️ Assinatura do Responsável</Text>
            {assinatura ? (
              <View style={styles.assinaturaContainer}>
                <Image source={{ uri: assinatura }} style={styles.assinaturaImage} resizeMode="contain" />
                <View style={{ flexDirection: 'row', gap: 12, marginTop: 12 }}>
                  <TouchableOpacity onPress={() => setAssinatura(null)} style={styles.clearBtn}><IconSymbol name="arrow.counterclockwise" size={16} color="#F43F5E" /><Text style={styles.clearBtnText}>Refazer</Text></TouchableOpacity>
                  <TouchableOpacity onPress={() => setShowSignModal(true)} style={styles.editSignBtn}><IconSymbol name="pencil" size={16} color="#60A5FA" /><Text style={styles.editSignBtnText}>Editar</Text></TouchableOpacity>
                </View>
              </View>
            ) : (
              <TouchableOpacity style={styles.signatureOpenBtn} onPress={() => setShowSignModal(true)}>
                 <IconSymbol name="signature" size={28} color="#94A3B8" />
                 <Text style={styles.signatureOpenBtnTitle}>Toque para Assinar</Text>
              </TouchableOpacity>
            )}
          </View>
        )}

        {/* ----------------- ABA DOCUMENTOS ----------------- */}
        {activeMenu === 'docs' && (
           <View style={styles.tabContent}>
             <Text style={styles.sectionTitle}>📄 Documentos</Text>
             <Text style={styles.hintText2}>Traga planilhas ou PDFs se necessário.</Text>
             
             <TouchableOpacity style={styles.addPhotoBox} onPress={async () => {
               try {
                 const res = await DocumentPicker.getDocumentAsync({ copyToCacheDirectory: true });
                 if (!res.canceled && res.assets) {
                   setDocumentos(prev => [...prev, { uri: res.assets[0].uri, name: res.assets[0].name }]);
                 }
               } catch (e) {
                 console.log(e);
               }
             }}>
               <IconSymbol name="folder.fill.badge.plus" size={28} color="#94A3B8" />
               <Text style={styles.addPhotoBoxText}>Anexar Arquivo</Text>
             </TouchableOpacity>

             {documentos.map((doc, i) => (
               <View key={i} style={styles.docItem}>
                  <IconSymbol name="doc.fill" size={20} color="#60A5FA" />
                  <Text style={styles.docItemText} numberOfLines={1}>{doc.name}</Text>
                  <TouchableOpacity onPress={() => setDocumentos(d => d.filter((_, idx) => idx !== i))}>
                    <IconSymbol name="trash.fill" size={18} color="#F43F5E" />
                  </TouchableOpacity>
               </View>
             ))}
           </View>
        )}

        {/* ----------------- ABA AJUDA ----------------- */}
        {activeMenu === 'ajuda' && (
           <View style={styles.tabContent}>
             <Text style={styles.sectionTitle}>❓ Precisa de Ajuda?</Text>
             <View style={styles.cardInfo}>
               <Text style={[styles.infoValue, { lineHeight: 22, color: '#94A3B8' }]}>
                 - Certifique-se de realizar o Check-in no local exato da visita para garantir a validade do GPS.{'\n\n'}
                 - Em caso de falha de conexão, os dados são salvos no celular e enviados automaticamente na próxima vez que abrir o aplicativo conectado.{'\n\n'}
                 - Problemas com o formulário? Relate um bug através das "Configurações".
               </Text>
             </View>
           </View>
        )}

        {!checkinFeito && (
          <Text style={styles.hintText}>⚠️ Faça o Check-in antes de enviar o relatório.</Text>
        )}

      </ScrollView>

      {/* Modal de Geofencing: Justificativa de Distância */}
      <Modal visible={showGeofenceModal} animationType="slide" transparent={true}>
        <View style={styles.geofenceOverlay}>
          <View style={styles.geofenceCard}>
            <View style={{ flexDirection: 'row', alignItems: 'center', gap: 10, marginBottom: 12 }}>
              <Text style={{ fontSize: 28 }}>📍</Text>
              <Text style={styles.geofenceTitle}>Check-in Fora do Raio</Text>
            </View>
            <Text style={styles.geofenceDesc}>
              Você parece estar a mais de 500 metros da empresa. Para continuar, explique o motivo:
            </Text>
            <TextInput
              style={styles.geofenceInput}
              placeholder="Ex: Reunião foi realizada na secretaria central..."
              placeholderTextColor="#64748B"
              value={justificativa}
              onChangeText={setJustificativa}
              multiline
              numberOfLines={4}
              textAlignVertical="top"
            />
            <View style={{ flexDirection: 'row', gap: 10, marginTop: 16 }}>
              <TouchableOpacity
                style={[styles.geofenceBtn, { backgroundColor: '#334155', flex: 1 }]}
                onPress={() => { setShowGeofenceModal(false); setPendingGps(null); }}
              >
                <Text style={{ color: '#94A3B8', fontWeight: '600' }}>Cancelar</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.geofenceBtn, { backgroundColor: '#3B82F6', flex: 2, opacity: justificativa.trim().length < 10 ? 0.5 : 1 }]}
                disabled={justificativa.trim().length < 10}
                onPress={async () => {
                  setShowGeofenceModal(false);
                  if (pendingGps) {
                    await executarCheckin(pendingGps, justificativa.trim());
                    setPendingGps(null);
                  }
                }}
              >
                <Text style={{ color: '#FFF', fontWeight: 'bold' }}>Confirmar Check-in</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>

      {/* Modal de Assinatura */}
      <Modal visible={showSignModal} animationType="slide" transparent={false}>
        <View style={styles.signModalContainer}>
          <View style={styles.signModalHeader}>
             <TouchableOpacity style={styles.signModalCancelBtn} onPress={() => setShowSignModal(false)}>
               <IconSymbol name="xmark" size={20} color="#94A3B8" />
               <Text style={styles.signModalCancelText}>Cancelar</Text>
             </TouchableOpacity>
             <Text style={styles.signModalTitle}>Assinatura</Text>
             <View style={{ width: 90 }} />
          </View>
          <Text style={styles.signInstruction}>Por favor, assine no quadro abaixo usando o dedo.</Text>
          <View style={styles.signCanvasWrapper}>
            <SignatureScreen
              webStyle={`
                 .m-signature-pad { box-shadow: none; border: none; }
                 .m-signature-pad--body { border: none; position: relative; }
                 .m-signature-pad--body::after {
                    content: "Assine acima da linha";
                    position: absolute;
                    bottom: 25%;
                    left: 10%;
                    right: 10%;
                    text-align: center;
                    color: #94A3B8;
                    font-size: 14px;
                    border-top: 2px dashed #94A3B8;
                    padding-top: 4px;
                    pointer-events: none;
                 }
              `}
              onOK={(signature) => {
                setAssinatura(signature);
                setShowSignModal(false);
              }}
              onEmpty={() => Alert.alert('Atenção', 'A assinatura está vazia.')}
              descriptionText="Assine aqui"
              clearText="Limpar"
              confirmText="Salvar"
              autoClear={true}
            />
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0F172A' },
  scrollContent: { padding: 20, paddingBottom: 60 },
  header: { flexDirection: 'row', alignItems: 'center', marginBottom: 24, gap: 12 },
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
  schoolName: { fontSize: 20, fontWeight: 'bold', color: '#F8FAFC' },
  visitaDate: { fontSize: 13, color: '#94A3B8', marginTop: 2 },
  checkinBtn: {
    flexDirection: 'row', alignItems: 'center', gap: 10,
    backgroundColor: '#3B82F6', padding: 16, borderRadius: 14, marginBottom: 28,
    shadowColor: '#3B82F6', shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.35, shadowRadius: 8, elevation: 5,
  },
  checkinBtnDone: { backgroundColor: '#059669' },
  checkinText: { color: '#FFF', fontWeight: 'bold', fontSize: 16 },
  sectionTitle: { fontSize: 18, fontWeight: 'bold', color: '#F8FAFC', marginBottom: 16 },
  fieldContainer: { marginBottom: 20 },
  label: { color: '#CBD5E1', fontSize: 14, fontWeight: '600', marginBottom: 8 },
  input: {
    backgroundColor: '#1E293B', color: '#F8FAFC', borderRadius: 12,
    padding: 14, fontSize: 15,
    borderWidth: 1, borderColor: 'rgba(255,255,255,0.06)',
  },
  inputLong: { height: 100, textAlignVertical: 'top' },
  switchRow: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    backgroundColor: '#1E293B', padding: 16, borderRadius: 12, marginBottom: 14,
    borderWidth: 1, borderColor: 'rgba(255,255,255,0.06)',
  },
  switchLabel: { color: '#CBD5E1', fontSize: 14, fontWeight: '600', flex: 1, marginRight: 12 },
  opcoesContainer: { flexDirection: 'row', flexWrap: 'wrap', gap: 10 },
  opcaoBtn: {
    paddingHorizontal: 16, paddingVertical: 10, borderRadius: 99,
    backgroundColor: '#1E293B', borderWidth: 1, borderColor: 'rgba(255,255,255,0.1)',
  },
  opcaoBtnSelected: { backgroundColor: '#2563EB', borderColor: '#2563EB' },
  opcaoText: { color: '#94A3B8', fontSize: 14 },
  opcaoTextSelected: { color: '#FFF', fontWeight: '600' },
  emptyBox: { padding: 24, alignItems: 'center' },
  emptyText: { color: '#94A3B8', textAlign: 'center', lineHeight: 22 },
  submitBtn: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 10,
    backgroundColor: '#059669', padding: 18, borderRadius: 14, marginTop: 12,
  },
  submitBtnDisabled: { backgroundColor: '#1E293B', opacity: 0.5 },
  submitText: { color: '#FFF', fontWeight: 'bold', fontSize: 17 },
  hintText: { color: '#F59E0B', textAlign: 'center', marginTop: 12, fontSize: 13 },
  signatureWrapper: { height: 250, borderRadius: 12, overflow: 'hidden', borderWidth: 1, borderColor: '#334155', backgroundColor: '#1E293B' },
  assinaturaContainer: { backgroundColor: '#1E293B', borderRadius: 12, padding: 16, alignItems: 'center', borderWidth: 1, borderColor: 'rgba(255, 255, 255, 0.1)' },
  assinaturaImage: { width: '100%', height: 150, backgroundColor: '#FFF', borderRadius: 8, marginBottom: 16 },
  clearBtn: { paddingVertical: 8, paddingHorizontal: 16, borderWidth: 1, borderColor: '#F43F5E', borderRadius: 8 },
  clearBtnText: { color: '#F43F5E', fontWeight: 'bold' },
  hintText2: { color: '#64748B', fontSize: 13, marginBottom: 12 },
  addPhotoBox: {
    borderWidth: 2, borderStyle: 'dashed', borderColor: '#334155', borderRadius: 12,
    padding: 24, alignItems: 'center', justifyContent: 'center', backgroundColor: '#0F172A',
    marginBottom: 16
  },
  addPhotoBoxText: { color: '#94A3B8', marginTop: 8, fontWeight: '500' },
  fotosContainer: { flexDirection: 'row', flexWrap: 'wrap', gap: 12, marginBottom: 20 },
  miniFotoWrapper: { position: 'relative' },
  miniFoto: { width: 80, height: 80, borderRadius: 8, borderWidth: 1, borderColor: '#334155' },
  remMiniFotoBtn: { position: 'absolute', top: -6, right: -6, backgroundColor: '#EF4444', borderRadius: 12, width: 22, height: 22, alignItems: 'center', justifyContent: 'center' },

  // Botão de abrir assinatura
  signatureOpenBtn: {
    borderWidth: 2,
    borderStyle: 'dashed',
    borderColor: 'rgba(59, 130, 246, 0.4)',
    borderRadius: 16,
    padding: 32,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'rgba(59, 130, 246, 0.06)',
    gap: 10,
    marginBottom: 8,
  },
  signatureOpenBtnTitle: {
    color: '#F8FAFC',
    fontSize: 18,
    fontWeight: 'bold',
  },
  signatureOpenBtnSub: {
    color: '#64748B',
    fontSize: 13,
    textAlign: 'center',
  },

  // Botões após assinatura
  editSignBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderWidth: 1,
    borderColor: 'rgba(96, 165, 250, 0.4)',
    borderRadius: 8,
    backgroundColor: 'rgba(59, 130, 246, 0.1)',
  },
  editSignBtnText: {
    color: '#60A5FA',
    fontWeight: 'bold',
  },

  // Modal de assinatura
  signModalContainer: {
    flex: 1,
    backgroundColor: '#0F172A',
  },
  signModalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingTop: 52,
    paddingBottom: 16,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255,255,255,0.06)',
    backgroundColor: '#0F172A',
  },
  signModalCancelBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    width: 90,
  },
  signModalCancelText: {
    color: '#94A3B8',
    fontSize: 16,
  },
  signModalTitle: {
    fontSize: 17,
    fontWeight: 'bold',
    color: '#F8FAFC',
    textAlign: 'center',
  },
  signInstruction: {
    textAlign: 'center',
    color: '#64748B',
    fontSize: 14,
    paddingVertical: 12,
    paddingHorizontal: 20,
  },
  signCanvasWrapper: {
    flex: 1,
    margin: 16,
    borderRadius: 16,
    overflow: 'hidden',
    backgroundColor: '#1E293B',
  },
  menuContainer: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 20, backgroundColor: '#1E293B', borderRadius: 14, overflow: 'hidden' },
  menuBtn: { flex: 1, paddingVertical: 14, alignItems: 'center', justifyContent: 'center', gap: 6 },
  menuBtnActive: { backgroundColor: '#3B82F6' },
  menuBtnText: { color: '#94A3B8', fontSize: 13, fontWeight: '600' },
  menuBtnTextActive: { color: '#FFF' },
  tabContent: { flex: 1, minHeight: 300 },
  cardInfo: { backgroundColor: '#1E293B', borderRadius: 12, padding: 18, borderWidth: 1, borderColor: 'rgba(255,255,255,0.06)' },
  infoRow: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 12 },
  infoLabel: { color: '#94A3B8', fontSize: 15, fontWeight: '500' },
  infoValue: { color: '#F8FAFC', fontSize: 15, fontWeight: '600' },
  docItem: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#1E293B', padding: 14, borderRadius: 12, marginBottom: 10, borderWidth: 1, borderColor: 'rgba(255,255,255,0.06)' },
  docItemText: { flex: 1, color: '#F8FAFC', marginHorizontal: 10, fontSize: 14 },

  // Modal de Geofencing
  geofenceOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.75)',
    justifyContent: 'flex-end',
  },
  geofenceCard: {
    backgroundColor: '#1E293B',
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    padding: 24,
    paddingBottom: 40,
    borderWidth: 1,
    borderColor: 'rgba(239,68,68,0.3)',
  },
  geofenceTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#F8FAFC',
  },
  geofenceDesc: {
    color: '#94A3B8',
    fontSize: 14,
    lineHeight: 22,
    marginBottom: 16,
  },
  geofenceInput: {
    backgroundColor: '#0F172A',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.08)',
    color: '#F8FAFC',
    padding: 14,
    fontSize: 15,
    minHeight: 100,
  },
  geofenceBtn: {
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
});

