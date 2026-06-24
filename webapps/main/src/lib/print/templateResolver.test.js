import { describe, it, expect, vi } from 'vitest';
import { slugify, encodeExpression, decodeExpression, resolveExpression } from './templateResolver.js';

const mockCtx = {
  getPresetValue: (key) => ({ 'product.code': 'ABC', 'serial.qt': '10' }[key]),
  getCustomFieldValue: (key) => ({ 'abc123': 'Red' }[key]),
};

describe('slugify', () => {
  it('converts spaces to underscores and lowercases', () => {
    expect(slugify('Product Color')).toBe('product_color');
  });

  it('removes parentheses and their contents', () => {
    expect(slugify('Qty (pcs)')).toBe('qty');
  });

  it('trims and collapses multiple underscores', () => {
    expect(slugify('  Hello__World  ')).toBe('hello_world');
  });
});

describe('encodeExpression', () => {
  it('replaces custom field name with _key', () => {
    expect(
      encodeExpression('{{cf::product_color}}', [{ name: 'Product Color', _key: 'abc123' }])
    ).toBe('{{cf::abc123}}');
  });

  it('passes through preset expressions unchanged', () => {
    expect(encodeExpression('Product: {{product.code}}', [])).toBe('Product: {{product.code}}');
  });
});

describe('decodeExpression', () => {
  it('replaces _key with custom field slug', () => {
    expect(
      decodeExpression('{{cf::abc123}}', [{ name: 'Product Color', _key: 'abc123' }])
    ).toBe('{{cf::product_color}}');
  });

  it('passes through preset expressions unchanged', () => {
    expect(decodeExpression('Product: {{product.code}}', [])).toBe('Product: {{product.code}}');
  });
});

describe('resolveExpression', () => {
  it('resolves preset variables using getPresetValue', () => {
    expect(
      resolveExpression('Product: {{product.code}} - Qty: {{serial.qt}} pcs', mockCtx, [])
    ).toBe('Product: ABC - Qty: 10 pcs');
  });

  it('strips the documented preset. prefix before getPresetValue', () => {
    // Regression: barcode {{preset.serial.qt}} rendered empty because the raw
    // token (incl. prefix) was passed to getPresetValue, which keys on bare names.
    expect(
      resolveExpression('(01)08057592610003(21){{preset.serial.qt}}', mockCtx, [])
    ).toBe('(01)08057592610003(21)10');
  });

  it('resolves custom field variables using getCustomFieldValue', () => {
    expect(
      resolveExpression('{{cf::abc123}}', mockCtx, [{ _key: 'abc123' }])
    ).toBe('Red');
  });

  it('resolves missing variable to empty string', () => {
    expect(
      resolveExpression('{{missing.var}}', mockCtx, [])
    ).toBe('');
  });

  it('resolves field:: tokens from formModel', () => {
    const fm = { QT: '12', 'Data Code': '14/2027' };
    expect(
      resolveExpression('QT: {{field::QT}}, DC: {{field::Data Code}}', mockCtx, [], fm)
    ).toBe('QT: 12, DC: 14/2027');
  });

  it('resolves field:: tokens with spaces in names', () => {
    const fm = { 'Shelf Life': '14/2028' };
    expect(
      resolveExpression('{{field::Shelf Life}}', mockCtx, [], fm)
    ).toBe('14/2028');
  });

  it('resolves field:: to empty when formModel is not provided', () => {
    expect(
      resolveExpression('{{field::QT}}', mockCtx, [])
    ).toBe('');
  });

  it('mixes preset, cf, and field:: tokens in one expression', () => {
    const fm = { QT: '5' };
    expect(
      resolveExpression('{{product.code}} x{{field::QT}} ({{cf::abc123}})', mockCtx, [{ _key: 'abc123' }], fm)
    ).toBe('ABC x5 (Red)');
  });
});
