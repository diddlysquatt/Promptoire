// @ts-nocheck
import React from 'react';
import { render, fireEvent } from '@testing-library/react';
import RadioTile from './RadioTile';

describe('RadioTile', () => {
  test('changes selection on click', () => {
    let val = 'a';
    const onChange = (v: string) => {
      val = v;
    };
    const { getByLabelText, rerender } = render(
      <RadioTile
        name="grp"
        value={val}
        onChange={onChange}
        options={[{ label: 'Option A', value: 'a' }, { label: 'Option B', value: 'b' }]}
        aria-label="tiles"
      />
    );
    const b = getByLabelText('Option B') as HTMLInputElement;
    fireEvent.click(b);
    rerender(
      <RadioTile
        name="grp"
        value={val}
        onChange={onChange}
        options={[{ label: 'Option A', value: 'a' }, { label: 'Option B', value: 'b' }]}
        aria-label="tiles"
      />
    );
    expect(val).toBe('b');
  });

  test('disabled prevents change', () => {
    let val = 'a';
    const onChange = (v: string) => {
      val = v;
    };
    const { getByLabelText } = render(
      <RadioTile
        name="grp"
        value={val}
        onChange={onChange}
        options={[{ label: 'Option A', value: 'a' }, { label: 'Option B', value: 'b' }]}
        disabled
        aria-label="tiles"
      />
    );
    const b = getByLabelText('Option B') as HTMLInputElement;
    fireEvent.click(b);
    expect(val).toBe('a');
  });
});


