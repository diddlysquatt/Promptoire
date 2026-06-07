// @ts-nocheck
import React from 'react';

export interface SwitchProps extends React.AriaAttributes {
  value: boolean;
  onChange: (nextValue: boolean) => void;
  disabled?: boolean;
  id?: string;
  name?: string;
  className?: string;
  label?: React.ReactNode;
}

/**
 * Accessible Switch component using role="switch" with keyboard support.
 */
export function Switch({
  value,
  onChange,
  disabled = false,
  id,
  name,
  className,
  label,
  ...aria
}: SwitchProps) {
  const handleToggle = React.useCallback(() => {
    if (disabled) return;
    onChange(!value);
  }, [disabled, onChange, value]);

  const handleKeyDown = (event: React.KeyboardEvent<HTMLButtonElement>) => {
    if (disabled) return;
    if (event.key === ' ' || event.key === 'Enter') {
      event.preventDefault();
      onChange(!value);
    }
  };

  const trackColor = disabled ? '#d1d5db' : value ? '#22c55e' : '#9ca3af';
  const thumbTranslate = value ? 'translateX(18px)' : 'translateX(0)';

  return (
    <button
      type="button"
      role="switch"
      aria-checked={value}
      aria-disabled={disabled || undefined}
      id={id}
      name={name}
      className={className}
      onClick={handleToggle}
      onKeyDown={handleKeyDown}
      disabled={disabled}
      {...aria}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 8,
        background: 'transparent',
        border: 'none',
        padding: 0,
        cursor: disabled ? 'not-allowed' : 'pointer',
      }}
    >
      <span
        aria-hidden
        style={{
          position: 'relative',
          width: 36,
          height: 20,
          backgroundColor: trackColor,
          borderRadius: 9999,
          transition: 'background-color 120ms ease',
          boxSizing: 'border-box',
        }}
      >
        <span
          style={{
            position: 'absolute',
            top: 2,
            left: 2,
            width: 16,
            height: 16,
            borderRadius: '50%',
            backgroundColor: '#ffffff',
            boxShadow: '0 1px 3px rgba(0,0,0,0.25)',
            transform: thumbTranslate,
            transition: 'transform 120ms ease',
          }}
        />
      </span>
      {label ? (
        <span style={{ userSelect: 'none', color: disabled ? '#9ca3af' : '#111827' }}>{label}</span>
      ) : null}
    </button>
  );
}

export default Switch;


