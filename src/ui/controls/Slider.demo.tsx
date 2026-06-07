// @ts-nocheck
import React from 'react';
import Slider, { SliderUnit } from './Slider';

export default function SliderDemo() {
  const [val, setVal] = React.useState(25);
  const [unit, setUnit] = React.useState<SliderUnit>('%');
  return (
    <div style={{ padding: 16, maxWidth: 400 }}>
      <Slider
        value={val}
        onChange={setVal}
        min={0}
        max={unit === '%' ? 100 : 800}
        step={1}
        showTicks
        unit={unit}
        onUnitChange={setUnit}
        aria-label="demo-slider"
        label={`Size (${unit})`}
      />
    </div>
  );
}


