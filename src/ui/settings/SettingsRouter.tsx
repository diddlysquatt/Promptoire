// @ts-nocheck
import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { SETTINGS_NAV_ITEMS, DEFAULT_SETTINGS_ROUTE } from '../../types/SettingsNav';
import SettingsLayout from './layout/SettingsLayout';
import Sidebar from './Sidebar';
import AboutPage from './pages/About/AboutPage';

const PageStub: React.FC<{ title: string }> = ({ title }) => (
  <section>
    <h1>{title}</h1>
  </section>
);

export const SettingsRouter: React.FC<{ onRequestClose?: () => void }> = ({ onRequestClose }) => {
  return (
    <Routes>
      <Route path="/settings" element={<SettingsLayout onRequestClose={onRequestClose} sidebar={<Sidebar />} />}>
        <Route index element={<Navigate to="general" replace />} />
        {SETTINGS_NAV_ITEMS.map((item) => (
          item.key === 'about'
            ? <Route key={item.key} path={item.path.replace('/settings/', '')} element={<AboutPage />} />
            : <Route key={item.key} path={item.path.replace('/settings/', '')} element={<PageStub title={item.label} />} />
        ))}
      </Route>
      <Route path="/settings/*" element={<Navigate to={DEFAULT_SETTINGS_ROUTE} replace />} />
    </Routes>
  );
};

export default SettingsRouter;


