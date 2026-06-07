// @ts-nocheck
import React from 'react';
import { NavLink } from 'react-router-dom';
import { SETTINGS_NAV_ITEMS } from '../../types/SettingsNav';

export const Sidebar: React.FC = () => {
  return (
    <nav className="settings-nav">
      <ul>
        {SETTINGS_NAV_ITEMS.map((item) => (
          <li key={item.key}>
            <NavLink
              to={item.path}
              className={({ isActive }) =>
                isActive ? 'settings-nav-link active' : 'settings-nav-link'
              }
            >
              {item.label}
            </NavLink>
          </li>
        ))}
      </ul>
    </nav>
  );
};

export default Sidebar;


