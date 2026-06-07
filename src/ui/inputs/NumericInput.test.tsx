// @ts-nocheck
import React from 'react';
import { render, fireEvent } from '@testing-library/react';
import NumericInput from './NumericInput';

describe('NumericInput', () => {
  test('ArrowUp/ArrowDown adjust by step and Shift by step*5', () => {
    let val = 0;
    const onChange = (n: number) => {
      val = n;
    };
    const { getByRole, rerender } = render(
      <NumericInput value={val} onChange={onChange} step={2} aria-label="num" />
    );
    const input = getByRole('textbox') as HTMLInputElement;

    fireEvent.keyDown(input, { key: 'ArrowUp' });
    rerender(<NumericInput value={val} onChange={onChange} step={2} aria-label="num" />);
    expect(val).toBe(2);

    fireEvent.keyDown(input, { key: 'ArrowDown' });
    rerender(<NumericInput value={val} onChange={onChange} step={2} aria-label="num" />);
    expect(val).toBe(0);

    fireEvent.keyDown(input, { key: 'ArrowUp', shiftKey: true });
    rerender(<NumericInput value={val} onChange={onChange} step={2} aria-label="num" />);
    expect(val).toBe(10);
  });

  test('disabled prevents keyboard changes', () => {
    let val = 0;
    const onChange = (n: number) => {
      val = n;
    };
    const { getByRole, rerender } = render(
      <NumericInput value={val} onChange={onChange} step={2} disabled aria-label="num" />
    );
    const input = getByRole('textbox') as HTMLInputElement;

    fireEvent.keyDown(input, { key: 'ArrowUp' });
    rerender(<NumericInput value={val} onChange={onChange} step={2} disabled aria-label="num" />);
    expect(val).toBe(0);
  });
});


