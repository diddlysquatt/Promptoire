// @ts-nocheck
import React from 'react';
import FilePicker from '../../../controls/FilePicker';
import { exportSettings, importSettings } from '../../../../persistence/settingsStorage';
import { showToast } from '../../../feedback/Toast';
import { reloadFromPersisted } from '../../../../state/settingsStore';

export const AboutPage: React.FC = () => {
  const [file, setFile] = React.useState<File | null>(null);
  const coffeeUrl = 'https://buy.stripe.com/cNiaEW3c0bsxcTL9gV3ZK00';

  const onExport = async () => {
    try {
      const blob = exportSettings();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'settings.json';
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
      showToast('Exported settings');
    } catch (e) {
      console.error(e);
      showToast('Export failed', { type: 'error' });
    }
  };

  const onImport = async () => {
    if (!file) return;
    try {
      await importSettings(file);
      reloadFromPersisted();
      showToast('Imported settings');
    } catch (e) {
      console.error(e);
      showToast('Import failed', { type: 'error' });
    }
  };

  return (
    <section>
      <h1>About</h1>
      <p>Export or import your settings JSON. Backward compatibility supported via migration.</p>
      <div style={{ display: 'grid', gap: 12, maxWidth: 560 }}>
        <button type="button" onClick={onExport} style={{ padding: '8px 12px', background: '#fff', border: '1px solid #d1d5db', borderRadius: 6 }}>Export Settings</button>
        <div>
          <FilePicker value={file} onChange={setFile} accept="application/json" />
          <button type="button" onClick={onImport} disabled={!file} style={{ marginTop: 8, padding: '8px 12px', background: '#fff', border: '1px solid #d1d5db', borderRadius: 6 }}>Import Settings</button>
        </div>
        <button
          type="button"
          onClick={() => window.open(coffeeUrl, '_blank', 'noopener,noreferrer')}
          style={{ padding: '8px 12px', background: '#f59e0b', color: '#fff', border: 'none', borderRadius: 6 }}
        >
          ☕ Buy Me a Coffee
        </button>
      </div>
    </section>
  );
};

export default AboutPage;


