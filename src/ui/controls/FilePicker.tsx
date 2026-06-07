// @ts-nocheck
import React from 'react';

export interface FilePickerProps extends React.AriaAttributes {
  value: File | null;
  onChange: (file: File | null) => void;
  disabled?: boolean;
  id?: string;
  name?: string;
  className?: string;
  accept?: string;
  onOpenFolder?: () => void;
}

export default function FilePicker({
  value,
  onChange,
  disabled = false,
  id,
  name,
  className,
  accept,
  onOpenFolder,
  ...aria
}: FilePickerProps) {
  const inputRef = React.useRef<HTMLInputElement | null>(null);

  const onSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files[0]) {
      onChange(files[0]);
    }
  };

  const previewUrl = React.useMemo(() => {
    if (!value) return null;
    if (value.type.startsWith('image/')) {
      return URL.createObjectURL(value);
    }
    return null;
  }, [value]);

  React.useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
  }, [previewUrl]);

  return (
    <div className={className} style={{ display: 'grid', gap: 8 }}>
      <input
        ref={inputRef}
        type="file"
        id={id}
        name={name}
        accept={accept}
        onChange={onSelect}
        disabled={disabled}
        aria-disabled={disabled || undefined}
        style={{ display: 'none' }}
        {...aria}
      />
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <button
          type="button"
          onClick={() => inputRef.current?.click()}
          disabled={disabled}
          style={{ padding: '6px 10px', border: '1px solid #d1d5db', borderRadius: 6, background: '#fff' }}
        >
          Choose File
        </button>
        {value ? <span>{value.name}</span> : <span>No file selected</span>}
        <div style={{ marginLeft: 'auto', display: 'flex', gap: 8 }}>
          <button
            type="button"
            onClick={() => onChange(null)}
            disabled={disabled || !value}
            aria-label="Clear file"
            style={{ padding: '6px 10px', border: '1px solid #d1d5db', borderRadius: 6, background: '#fff' }}
          >
            Clear
          </button>
          <button
            type="button"
            onClick={() => onOpenFolder && onOpenFolder()}
            disabled={disabled || !onOpenFolder}
            aria-label="Open folder"
            style={{ padding: '6px 10px', border: '1px solid #d1d5db', borderRadius: 6, background: '#fff' }}
          >
            Open Folder
          </button>
        </div>
      </div>
      {previewUrl ? (
        <div style={{ width: 96, height: 96, border: '1px solid #e5e7eb', borderRadius: 6, overflow: 'hidden' }}>
          <img src={previewUrl} alt="Selected file preview" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
        </div>
      ) : null}
    </div>
  );
}


