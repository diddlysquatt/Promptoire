// @ts-nocheck
import React from 'react';
import { render, fireEvent } from '@testing-library/react';
import { Switch } from './Switch';

describe('Switch', () => {
  test('toggles on click', () => {
    const onChange = jest.fn();
    const { getByRole } = render(<Switch value={false} onChange={onChange} aria-label="switch" />);
    const button = getByRole('switch');
    fireEvent.click(button);
    expect(onChange).toHaveBeenCalledWith(true);
  });

  test('toggles on Space and Enter', () => {
    const onChange = jest.fn();
    const { getByRole } = render(<Switch value={false} onChange={onChange} aria-label="switch" />);
    const button = getByRole('switch');
    fireEvent.keyDown(button, { key: ' ' });
    expect(onChange).toHaveBeenCalledWith(true);
    fireEvent.keyDown(button, { key: 'Enter' });
    expect(onChange).toHaveBeenCalledWith(true);
  });

  test('disabled prevents change', () => {
    const onChange = jest.fn();
    const { getByRole } = render(<Switch value={false} onChange={onChange} aria-label="switch" disabled />);
    const button = getByRole('switch');
    fireEvent.click(button);
    fireEvent.keyDown(button, { key: 'Enter' });
    expect(onChange).not.toHaveBeenCalled();
  });
});


