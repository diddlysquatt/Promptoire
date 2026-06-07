// @ts-nocheck
import React from 'react';
import NumericInput from '../inputs/NumericInput';

export type SliderUnit = '%' | 'px';

export interface SliderProps extends React.AriaAttributes {
  value: number;
  onChange: (nextValue: number) => void;
  min?: number;
  max?: number;
  step?: number;
  disabled?: boolean;
  showTicks?: boolean;
  unit?: SliderUnit;
  onUnitChange?: (unit: SliderUnit) => void;
  id?: string;
  name?: string;
  className?: string;
  label?: React.ReactNode;
}

function clamp(value: number, min?: number, max?: number) {
  let result = value;
  if (typeof min === 'number') result = Math.max(result, min);
  if (typeof max === 'number') result = Math.min(result, max);
  return result;
}

export default function Slider({
  value,
  onChange,
  min = 0,
  max = 100,
  step = 1,
  disabled = false,
  showTicks = false,
  unit = '%',
  onUnitChange,
  id,
  name,
  className,
  label,
  ...aria
}: SliderProps) {
  const inputRef = React.useRef<HTMLInputElement | null>(null);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (disabled) return;
    const delta = e.shiftKey ? 5 : 1;
    if (e.key === 'ArrowRight' || e.key === 'ArrowUp') {
      e.preventDefault();
      onChange(clamp(value + delta, min, max));
    } else if (e.key === 'ArrowLeft' || e.key === 'ArrowDown') {
      e.preventDefault();
      onChange(clamp(value - delta, min, max));
    }
  };

  const ticks = React.useMemo(() => {
    if (!showTicks) return null;
    const count = Math.floor((max - min) / step);
    const nodes = [] as React.ReactNode[];
    for (let i = 0; i <= count; i++) {
      const left = (i / count) * 100;
      nodes.push(
        <span key={i} style={{ position: 'absolute', left: `${left}%`, top: 0, bottom: 0, width: 1, background: '#e5e7eb' }} aria-hidden />
      );
    }
    return <div aria-hidden style={{ position: 'relative', height: 12 }}>{nodes}</div>;
  }, [showTicks, max, min, step]);

  const trackPercent = ((value - min) / (max - min)) * 100;

  const unitToggle = (
    <button
      type="button"
      onClick={() => onUnitChange && onUnitChange(unit === '%' ? 'px' : '%')}
      disabled={disabled || !onUnitChange}
      aria-label="Toggle unit"
      style={{
        padding: '4px 8px',
        borderRadius: 6,
        border: '1px solid #d1d5db',
        background: '#fff',
        cursor: disabled ? 'not-allowed' : 'pointer',
      }}
    >
      {unit}
    </button>
  );

  return (
    <div className={className} style={{ display: 'grid', gap: 8 }}>
      {label ? <label htmlFor={id ? `${id}__range` : undefined} style={{ userSelect: 'none' }}>{label}</label> : null}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr auto auto', alignItems: 'center', gap: 8 }}>
        <div style={{ position: 'relative', height: 12 }}>
          {ticks}
          <div aria-hidden style={{ position: 'absolute', left: 0, right: 0, top: 5, height: 2, background: '#e5e7eb', borderRadius: 2 }} />
          <div aria-hidden style={{ position: 'absolute', left: 0, top: 5, height: 2, width: `${trackPercent}%`, background: '#60a5fa', borderRadius: 2 }} />
          <input
            ref={inputRef}
            type="range"
            id={id ? `${id}__range` : undefined}
            name={name}
            min={min}
            max={max}
            step={step}
            value={value}
            onChange={(e) => onChange(clamp(Number(e.target.value), min, max))}
            onKeyDown={handleKeyDown}
            disabled={disabled}
            aria-disabled={disabled || undefined}
            aria-valuemin={min}
            aria-valuemax={max}
            aria-valuenow={value}
            {...aria}
            style={{
              position: 'absolute',
              left: 0,
              right: 0,
              top: 0,
              bottom: 0,
              width: '100%',
              background: 'transparent',
            }}
          />
        </div>
        <NumericInput
          value={value}
          onChange={(n) => onChange(clamp(n, min, max))}
          min={min}
          max={max}
          step={step}
          disabled={disabled}
          suffix={unit}
          aria-label="Numeric value"
        />
        {unitToggle}
      </div>
    </div>
  );
}


