export type SettingsPageKey =
  | 'general'
  | 'appearance'
  | 'layout'
  | 'hotkeys'
  | 'text-fonts'
  | 'advanced'
  | 'about';

export interface SettingsNavItem {
  key: SettingsPageKey;
  label: string;
  path: string;
}

export const SETTINGS_NAV_ITEMS: ReadonlyArray<SettingsNavItem> = [
  { key: 'general', label: 'General', path: '/settings/general' },
  { key: 'appearance', label: 'Appearance', path: '/settings/appearance' },
  { key: 'layout', label: 'Layout', path: '/settings/layout' },
  { key: 'hotkeys', label: 'Hotkeys', path: '/settings/hotkeys' },
  { key: 'text-fonts', label: 'Text & Fonts', path: '/settings/text-fonts' },
  { key: 'advanced', label: 'Advanced', path: '/settings/advanced' },
  { key: 'about', label: 'About', path: '/settings/about' }
];

export const DEFAULT_SETTINGS_ROUTE = '/settings/general';


