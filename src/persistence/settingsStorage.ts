// Versioned settings storage with export/import and migration hook

export type SettingsSchemaVersion = 1;

export const CURRENT_SETTINGS_VERSION: SettingsSchemaVersion = 1;

export type SettingsSlices = {
  general: Record<string, any>;
  appearance: Record<string, any>;
  layout: Record<string, any>;
  hotkeys: Record<string, any>;
  textFonts: Record<string, any>;
  advanced: Record<string, any>;
};

export type VersionedSettings = {
  __version: SettingsSchemaVersion;
  data: SettingsSlices;
};

export type MigrationContext = {
  fromVersion: number;
  toVersion: number;
};

export type SettingsMigrator = (input: any, ctx: MigrationContext) => VersionedSettings;

let migrator: SettingsMigrator | null = null;

export function registerSettingsMigrator(fn: SettingsMigrator) {
  migrator = fn;
}

// Defaults can be provided by app; we include minimal placeholders
export const DEFAULT_SETTINGS: SettingsSlices = {
  general: {},
  appearance: {},
  layout: {},
  hotkeys: {},
  textFonts: {},
  advanced: {},
};

const STORAGE_KEY = 'app.settings.v1';

export function loadSettings(): VersionedSettings {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return { __version: CURRENT_SETTINGS_VERSION, data: DEFAULT_SETTINGS };
    const parsed = JSON.parse(raw);
    if (typeof parsed.__version !== 'number') {
      // Unversioned data, wrap it
      return { __version: CURRENT_SETTINGS_VERSION, data: parsed } as VersionedSettings;
    }
    if (parsed.__version === CURRENT_SETTINGS_VERSION) return parsed as VersionedSettings;
    if (migrator) {
      return migrator(parsed, {
        fromVersion: parsed.__version,
        toVersion: CURRENT_SETTINGS_VERSION,
      });
    }
    // Fallback: return defaults if no migrator available
    return { __version: CURRENT_SETTINGS_VERSION, data: DEFAULT_SETTINGS };
  } catch (e) {
    console.error('Failed to load settings', e);
    return { __version: CURRENT_SETTINGS_VERSION, data: DEFAULT_SETTINGS };
  }
}

export function saveSettings(data: SettingsSlices) {
  const wrapped: VersionedSettings = { __version: CURRENT_SETTINGS_VERSION, data };
  localStorage.setItem(STORAGE_KEY, JSON.stringify(wrapped));
}

export function exportSettings(): Blob {
  const current = loadSettings();
  const json = JSON.stringify(current, null, 2);
  return new Blob([json], { type: 'application/json' });
}

export async function importSettings(file: File): Promise<VersionedSettings> {
  const text = await file.text();
  const parsed = JSON.parse(text);
  // Accept older versions and migrate via hook
  if (typeof parsed.__version !== 'number') {
    // Assume raw slices; wrap and treat as older schema
    const wrapped = { __version: 0, data: parsed };
    if (migrator) {
      const migrated = migrator(wrapped, { fromVersion: 0, toVersion: CURRENT_SETTINGS_VERSION });
      saveSettings(migrated.data);
      return migrated;
    }
    const fallback = { __version: CURRENT_SETTINGS_VERSION, data: DEFAULT_SETTINGS };
    saveSettings(fallback.data);
    return fallback;
  }
  if (parsed.__version !== CURRENT_SETTINGS_VERSION) {
    if (migrator) {
      const migrated = migrator(parsed, { fromVersion: parsed.__version, toVersion: CURRENT_SETTINGS_VERSION });
      saveSettings(migrated.data);
      return migrated;
    }
    const fallback = { __version: CURRENT_SETTINGS_VERSION, data: DEFAULT_SETTINGS };
    saveSettings(fallback.data);
    return fallback;
  }
  saveSettings(parsed.data);
  return parsed as VersionedSettings;
}


