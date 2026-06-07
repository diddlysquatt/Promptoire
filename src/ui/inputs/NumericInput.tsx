// @ts-nocheck
import React from 'react';

export interface NumericInputProps extends React.AriaAttributes {
  value: number;
  onChange: (nextValue: number) => void;
  min?: number;
  max?: number;
  step?: number;
  disabled?: boolean;
  id?: string;
  name?: string;
  className?: string;
  suffix?: string;
  prefix?: string;
}

export function clamp(value: number, min?: number, max?: number) {
  let result = value;
  if (typeof min === 'number') result = Math.max(result, min);
  if (typeof max === 'number') result = Math.min(result, max);
  return result;
}

export default function NumericInput({
  value,
  onChange,
  min,
  max,
  step = 1,
  disabled = false,
  id,
  name,
  className,
  suffix,
  prefix,
  ...aria
}: NumericInputProps) {
  const [text, setText] = React.useState(String(value));

  React.useEffect(() => {
    setText(String(value));
  }, [value]);

  const commit = React.useCallback(
    (next: string) => {
      const parsed = Number(next);
      if (!Number.isNaN(parsed)) {
        const clamped = clamp(parsed, min, max);
        onChange(clamped);
      } else {
        setText(String(value));
      }
    },
    [min, max, onChange, value]
  );

  const onKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (disabled) return;
    const increment = e.shiftKey ? step * 5 : step;
    if (e.key === 'ArrowUp') {
      e.preventDefault();
      onChange(clamp(value + increment, min, max));
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      onChange(clamp(value - increment, min, max));
    } else if (e.key === 'Enter') {
      commit(text);
    }
  };

  return (
    <div className={className} style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
      {prefix ? <span aria-hidden>{prefix}</span> : null}
      <input
        type="text"
        inputMode="numeric"
        pattern="[0-9]*"
        value={text}
        onChange={(e) => setText(e.target.value)}
        onBlur={() => commit(text)}
        onKeyDown={onKeyDown}
        aria-disabled={disabled || undefined}
        disabled={disabled}
        id={id}
        name={name}
        {...aria}
        style={{
          width: 64,
          padding: '4px 8px',
          borderRadius: 6,
          border: '1px solid #d1d5db',
        }}
      />
      {suffix ? <span aria-hidden>{suffix}</span> : null}
    </div>
  );
}


