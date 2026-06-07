// @ts-nocheck
import React from 'react';
import { applyChanges, getDefaults, getDraftSlice, hasDiff, hasDiffForSlice, replaceDraftSlice, resetSliceToPersisted, restoreDefaultsSlice, reloadFromPersisted } from '../../state/settingsStore';
import { showToast } from '../feedback/Toast';

export interface SaveFooterProps {
  sectionKey: 'general' | 'appearance' | 'layout' | 'hotkeys' | 'textFonts' | 'advanced';
  disableSectionActions?: boolean;
}

export const SaveFooter: React.FC<SaveFooterProps> = ({ sectionKey, disableSectionActions }) => {
  const [, force] = React.useReducer((x) => x + 1, 0);

  React.useEffect(() => {
    // subscribe to store updates for live buttons state
    const unsub = require('../../state/settingsStore').subscribe(force);
    return () => unsub();
  }, []);

  const disabledApply = !hasDiff();
  const disabledResetSection = disableSectionActions || !hasDiffForSlice(sectionKey);
  const disabledRestoreDefaults = disableSectionActions || JSON.stringify(getDraftSlice(sectionKey)) === JSON.stringify(getDefaults()[sectionKey]);
  const disabledCancel = !hasDiff();

  const onApply = async () => {
    await applyChanges();
    showToast('Settings saved');
  };

  const onCancel = () => {
    reloadFromPersisted();
    showToast('Changes discarded');
  };

  const onResetSection = () => {
    resetSliceToPersisted(sectionKey);
  };

  const onRestoreDefaults = () => {
    restoreDefaultsSlice(sectionKey);
  };

  return (
    <div style={{ position: 'sticky', bottom: 0, background: 'rgba(255,255,255,0.9)', backdropFilter: 'saturate(180%) blur(8px)', borderTop: '1px solid #e5e7eb', padding: '10px 12px', display: 'flex', gap: 8 }}>
      <button type="button" onClick={onApply} disabled={disabledApply} aria-disabled={disabledApply || undefined} style={{ padding: '8px 12px', background: disabledApply ? '#e5e7eb' : '#2563eb', color: disabledApply ? '#6b7280' : '#fff', border: 'none', borderRadius: 6 }}>
        Accept
      </button>
      <div style={{ marginLeft: 'auto', display: 'flex', gap: 8 }}>
        <button type="button" onClick={onResetSection} disabled={disabledResetSection} aria-disabled={disabledResetSection || undefined} style={{ padding: '8px 12px', background: '#fff', border: '1px solid #d1d5db', borderRadius: 6 }}>
          Reset Section
        </button>
        <button type="button" onClick={onRestoreDefaults} disabled={disabledRestoreDefaults} aria-disabled={disabledRestoreDefaults || undefined} style={{ padding: '8px 12px', background: '#fff', border: '1px solid #d1d5db', borderRadius: 6 }}>
          Restore Defaults
        </button>
        <button type="button" onClick={onCancel} disabled={disabledCancel} aria-disabled={disabledCancel || undefined} style={{ padding: '8px 12px', background: '#fff', border: '1px solid #d1d5db', borderRadius: 6 }}>
          Cancel
        </button>
      </div>
    </div>
  );
};

export default SaveFooter;


