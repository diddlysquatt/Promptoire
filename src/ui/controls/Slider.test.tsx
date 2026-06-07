// @ts-nocheck
import React from 'react';
import { render, fireEvent } from '@testing-library/react';
import Slider from './Slider';

describe('Slider', () => {
  test('Arrow keys adjust by 1 and Shift+Arrow by 5', () => {
    let val = 10;
    const onChange = (n: number) => {
      val = n;
    };
    const { getByRole, rerender } = render(
      <Slider value={val} onChange={onChange} min={0} max={100} aria-label="slider" />
    );
    const range = getByRole('slider') as HTMLInputElement;

    fireEvent.keyDown(range, { key: 'ArrowRight' });
    rerender(<Slider value={val} onChange={onChange} min={0} max={100} aria-label="slider" />);
    expect(val).toBe(11);

    fireEvent.keyDown(range, { key: 'ArrowLeft' });
    rerender(<Slider value={val} onChange={onChange} min={0} max={100} aria-label="slider" />);
    expect(val).toBe(10);

    fireEvent.keyDown(range, { key: 'ArrowUp', shiftKey: true });
    rerender(<Slider value={val} onChange={onChange} min={0} max={100} aria-label="slider" />);
    expect(val).toBe(15);

    fireEvent.keyDown(range, { key: 'ArrowDown', shiftKey: true });
    rerender(<Slider value={val} onChange={onChange} min={0} max={100} aria-label="slider" />);
    expect(val).toBe(10);
  });

  test('disabled prevents keyboard changes', () => {
    let val = 10;
    const onChange = (n: number) => {
      val = n;
    };
    const { getByRole, rerender } = render(
      <Slider value={val} onChange={onChange} min={0} max={100} disabled aria-label="slider" />
    );
    const range = getByRole('slider') as HTMLInputElement;

    fireEvent.keyDown(range, { key: 'ArrowRight' });
    rerender(<Slider value={val} onChange={onChange} min={0} max={100} disabled aria-label="slider" />);
    expect(val).toBe(10);
  });
});


