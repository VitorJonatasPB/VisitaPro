// Fallback for using MaterialIcons on Android and web.

import MaterialIcons from '@expo/vector-icons/MaterialIcons';
import { SymbolWeight, SymbolViewProps } from 'expo-symbols';
import { ComponentProps } from 'react';
import { OpaqueColorValue, type StyleProp, type TextStyle } from 'react-native';

type IconMapping = Record<SymbolViewProps['name'], ComponentProps<typeof MaterialIcons>['name']>;
type IconSymbolName = keyof typeof MAPPING;

/**
 * Add your SF Symbols to Material Icons mappings here.
 * - see Material Icons in the [Icons Directory](https://icons.expo.fyi).
 * - see SF Symbols in the [SF Symbols](https://developer.apple.com/sf-symbols/) app.
 */
const MAPPING = {
  // Navegação
  'house.fill': 'home',
  'chevron.left': 'chevron-left',
  'chevron.right': 'chevron-right',
  'chevron.left.forwardslash.chevron.right': 'code',
  'xmark': 'close',
  'xmark.circle.fill': 'cancel',

  // Status / Ação
  'checkmark': 'check',
  'checkmark.circle': 'check-circle',
  'play.fill': 'play-arrow',
  'plus': 'add',
  'pencil': 'edit',
  'arrow.counterclockwise': 'refresh',

  // Comunicação / Info
  'paperplane.fill': 'send',
  'info.circle': 'info',
  'questionmark.circle': 'help',
  'lock.fill': 'lock',
  'person.fill': 'person',
  'gearshape.fill': 'settings',
  'signature': 'draw',

  // Localização / Rede
  'location.fill': 'location-on',
  'wifi.slash': 'wifi-off',

  // Calendário / Tempo
  'calendar': 'calendar-today',
  'calendar.badge.clock': 'event',
  'clock': 'schedule',

  // Documentos / Arquivos
  'doc.text': 'description',
  'doc.fill': 'insert-drive-file',
  'folder': 'folder',
  'folder.fill.badge.plus': 'create-new-folder',
  'trash.fill': 'delete',

  // Câmera / Mídia
  'camera.fill': 'photo-camera',

  // Busca
  'magnifyingglass': 'search',

  // Logout
  'rectangle.portrait.and.arrow.right': 'logout',

  // Personalização
  'moon.fill': 'dark-mode',
  'textformat.size': 'text-fields',
} as IconMapping;

/**
 * An icon component that uses native SF Symbols on iOS, and Material Icons on Android and web.
 * This ensures a consistent look across platforms, and optimal resource usage.
 * Icon `name`s are based on SF Symbols and require manual mapping to Material Icons.
 */
export function IconSymbol({
  name,
  size = 24,
  color,
  style,
}: {
  name: IconSymbolName;
  size?: number;
  color: string | OpaqueColorValue;
  style?: StyleProp<TextStyle>;
  weight?: SymbolWeight;
}) {
  return <MaterialIcons color={color} size={size} name={MAPPING[name]} style={style} />;
}
