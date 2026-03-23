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
});
