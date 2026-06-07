// @ts-nocheck
import { DEFAULT_SETTINGS, loadSettings, saveSettings } from '../persistence/settingsStorage';

export type SettingsSliceKey = 'general' | 'appearance' | 'layout' | 'hotkeys' | 'textFonts' | 'advanced';

export type SettingsDraft = {
  general: Record<string, any>;
  appearance: Record<string, any>;
  layout: Record<string, any>;
  hotkeys: Record<string, any>;
  textFonts: Record<string, any>;
  advanced: Record<string, any>;
};

type Listener = () => void;

const listeners = new Set<Listener>();

function notify() {
  listeners.forEach((fn) => {
    try { fn(); } catch {}
  });
}

function deepClone<T>(obj: T): T {
  return JSON.parse(JSON.stringify(obj));
}

function shallowMerge(target: Record<string, any>, patch: Record<string, any>) {
  Object.keys(patch).forEach((key) => {
    target[key] = patch[key];
  });
}

function deepEqual(a: any, b: any): boolean {
  if (a === b) return true;
  if (typeof a !== 'object' || typeof b !== 'object' || !a || !b) return false;
  const aKeys = Object.keys(a);
  const bKeys = Object.keys(b);
  if (aKeys.length !== bKeys.length) return false;
  for (const key of aKeys) {
    if (!deepEqual(a[key], b[key])) return false;
  }
  return true;
}

let persisted = loadSettings().data;
let draft: SettingsDraft = deepClone(persisted);

export function subscribe(listener: Listener) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export function getDraft(): SettingsDraft {
  return draft;
}

export function getPersisted(): SettingsDraft {
  return persisted;
}

export function getDefaults(): SettingsDraft {
  return DEFAULT_SETTINGS as SettingsDraft;
}

export function getDraftSlice<K extends SettingsSliceKey>(key: K): SettingsDraft[K] {
  return draft[key];
}

export function updateDraftSlice<K extends SettingsSliceKey>(key: K, patch: Partial<SettingsDraft[K]>) {
  const next = deepClone(draft);
  shallowMerge(next[key], patch as Record<string, any>);
  draft = next;
  notify();
}

export function replaceDraftSlice<K extends SettingsSliceKey>(key: K, value: SettingsDraft[K]) {
  const next = deepClone(draft);
  next[key] = deepClone(value);
  draft = next;
  notify();
}

export function resetSliceToPersisted<K extends SettingsSliceKey>(key: K) {
  const next = deepClone(draft);
  next[key] = deepClone(persisted[key]);
  draft = next;
  notify();
}

export function restoreDefaultsSlice<K extends SettingsSliceKey>(key: K) {
  const next = deepClone(draft);
  next[key] = deepClone(DEFAULT_SETTINGS[key]);
  draft = next;
  notify();
}

export function isSliceAtDefaults<K extends SettingsSliceKey>(key: K) {
  return deepEqual(draft[key], DEFAULT_SETTINGS[key]);
}

export function hasDiffForSlice<K extends SettingsSliceKey>(key: K) {
  return !deepEqual(draft[key], persisted[key]);
}

export function hasDiff(): boolean {
  return (
    hasDiffForSlice('general') ||
    hasDiffForSlice('appearance') ||
    hasDiffForSlice('layout') ||
    hasDiffForSlice('hotkeys') ||
    hasDiffForSlice('textFonts') ||
    hasDiffForSlice('advanced')
  );
}

export function reloadFromPersisted() {
  persisted = loadSettings().data;
  draft = deepClone(persisted);
  notify();
}

export async function applyChanges() {
  // Write full draft as current settings
  saveSettings(draft);
  // Update in-memory persisted and align draft to persisted
  persisted = deepClone(draft);
  notify();
}


