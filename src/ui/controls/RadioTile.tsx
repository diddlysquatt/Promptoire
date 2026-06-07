// @ts-nocheck
import React from 'react';

export interface RadioTileOption<T extends string | number> {
  label: React.ReactNode;
  value: T;
  description?: React.ReactNode;
}

export interface RadioTileProps<T extends string | number> extends React.AriaAttributes {
  name: string;
  value: T;
  onChange: (value: T) => void;
  options: RadioTileOption<T>[];
  disabled?: boolean;
  className?: string;
}

export default function RadioTile<T extends string | number>({
  name,
  value,
  onChange,
  options,
  disabled = false,
  className,
  ...aria
}: RadioTileProps<T>) {
  return (
    <div role="radiogroup" aria-disabled={disabled || undefined} className={className} {...aria} style={{ display: 'grid', gap: 8 }}>
      {options.map((opt) => {
        const selected = opt.value === value;
        return (
          <label
            key={String(opt.value)}
            style={{
              display: 'grid',
              gridTemplateColumns: 'auto 1fr',
              gap: 8,
              alignItems: 'start',
              padding: 8,
              border: '1px solid ' + (selected ? '#60a5fa' : '#e5e7eb'),
              borderRadius: 8,
              background: selected ? '#eff6ff' : '#fff',
              cursor: disabled ? 'not-allowed' : 'pointer',
            }}
          >
            <input
              type="radio"
              name={name}
              value={String(opt.value)}
              checked={selected}
              onChange={() => !disabled && onChange(opt.value)}
              disabled={disabled}
              style={{ marginTop: 3 }}
            />
            <div>
              <div style={{ fontWeight: 600 }}>{opt.label}</div>
              {opt.description ? <div style={{ color: '#6b7280' }}>{opt.description}</div> : null}
            </div>
          </label>
        );
      })}
    </div>
  );
}


