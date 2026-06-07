// @ts-nocheck
import React from 'react';
import { render, fireEvent } from '@testing-library/react';
import FilePicker from './FilePicker';

describe('FilePicker', () => {
  test('shows filename and clears', () => {
    const file = new File(['content'], 'test.png', { type: 'image/png' });
    let current: File | null = file;
    const onChange = (f: File | null) => {
      current = f;
    };
    const { getByText, rerender } = render(
      <FilePicker value={current} onChange={onChange} aria-label="picker" />
    );
    expect(getByText('test.png')).toBeTruthy();

    const clear = getByText('Clear');
    fireEvent.click(clear);
    rerender(<FilePicker value={current} onChange={onChange} aria-label="picker" />);
    expect(current).toBeNull();
  });

  test('disabled prevents clear and open folder', () => {
    const file = new File(['content'], 'test.png', { type: 'image/png' });
    let current: File | null = file;
    const onChange = jest.fn((f: File | null) => {
      current = f;
    });
    const onOpenFolder = jest.fn();
    const { getByText } = render(
      <FilePicker value={current} onChange={onChange} onOpenFolder={onOpenFolder} disabled aria-label="picker" />
    );
    fireEvent.click(getByText('Clear'));
    fireEvent.click(getByText('Open Folder'));
    expect(onChange).not.toHaveBeenCalled();
    expect(onOpenFolder).not.toHaveBeenCalled();
  });
});


