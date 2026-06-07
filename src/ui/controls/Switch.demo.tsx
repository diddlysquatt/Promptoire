// @ts-nocheck
import React from 'react';
import { Switch } from './Switch';

export default function SwitchDemo() {
  const [on, setOn] = React.useState(false);
  return (
    <div style={{ padding: 16 }}>
      <Switch value={on} onChange={setOn} aria-label="demo-switch" label={on ? 'On' : 'Off'} />
    </div>
  );
}


