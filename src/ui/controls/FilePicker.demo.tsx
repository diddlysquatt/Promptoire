// @ts-nocheck
import React from 'react';
import FilePicker from './FilePicker';

export default function FilePickerDemo() {
  const [file, setFile] = React.useState<File | null>(null);
  return (
    <div style={{ padding: 16 }}>
      <FilePicker value={file} onChange={setFile} aria-label="demo-picker" accept="image/*" onOpenFolder={() => alert('Open folder clicked')} />
    </div>
  );
}


