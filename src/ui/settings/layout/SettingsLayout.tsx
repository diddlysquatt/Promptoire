// @ts-nocheck
import React, { useEffect } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import SaveFooter from '../SaveFooter';

type SettingsLayoutProps = {
  onRequestClose?: () => void;
  sidebar: React.ReactNode;
};

export const SettingsLayout: React.FC<SettingsLayoutProps> = ({ onRequestClose, sidebar }) => {
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        if (onRequestClose) {
          onRequestClose();
        } else {
          // Fallback: navigate back if app doesn't provide close handler
          navigate(-1);
        }
      }
    }

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [navigate, onRequestClose]);

  return (
    <div className="settings-container" role="dialog" aria-modal="true" aria-label="Settings">
      <aside className="settings-sidebar" aria-label="Settings navigation">
        {sidebar}
      </aside>
      <main className="settings-content" tabIndex={-1}>
        <Outlet />
        {(() => {
          const pathname = location.pathname || '';
          const parts = pathname.split('/').filter(Boolean);
          const last = parts[parts.length - 1] || '';
          const map: Record<string, any> = {
            general: 'general',
            appearance: 'appearance',
            layout: 'layout',
            hotkeys: 'hotkeys',
            'text-fonts': 'textFonts',
            advanced: 'advanced',
          };
          const sectionKey = map[last];
          const disableSectionActions = !sectionKey || last === 'about';
          return (
            <SaveFooter sectionKey={sectionKey || 'general'} disableSectionActions={disableSectionActions} />
          );
        })()}
      </main>
    </div>
  );
};

export default SettingsLayout;


