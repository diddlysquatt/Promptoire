// @ts-nocheck
import React from 'react';
import RadioTile from './RadioTile';

export default function RadioTileDemo() {
  const [val, setVal] = React.useState('a');
  return (
    <div style={{ padding: 16, maxWidth: 420 }}>
      <RadioTile
        name="tile-demo"
        value={val}
        onChange={setVal}
        options={[
          { label: 'Option A', value: 'a', description: 'Alpha selection' },
          { label: 'Option B', value: 'b', description: 'Beta selection' },
        ]}
        aria-label="demo-tiles"
      />
    </div>
  );
}


