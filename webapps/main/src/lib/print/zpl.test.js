import { describe, it, expect, vi, beforeEach } from 'vitest';
import { generateZpl } from './zpl.js';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function makeTemplate(fields, pages = 1) {
  const schemas = [];
  for (let i = 0; i < pages; i++) {
    schemas.push(fields.map(f => ({ ...f })));
  }
  return { basePdf: '', schemas };
}

function makeField(overrides) {
  return {
    name: 'field1',
    type: 'text',
    position: { x: 10, y: 20 },
    width: 50,
    height: 10,
    fontSize: 12,
    alignment: 'left',
    content: '',
    ...overrides,
  };
}

// ---------------------------------------------------------------------------
// Envelope (ZPL-01, ZPL-05)
// ---------------------------------------------------------------------------

describe('Envelope', () => {
  it('single-page template returns string starting with ^XA and ending with ^XZ', () => {
    const template = makeTemplate([makeField()]);
    const result = generateZpl(template, [{}]);
    expect(result.trim().startsWith('^XA')).toBe(true);
    expect(result.trim().endsWith('^XZ')).toBe(true);
  });

  it('quantity=3 includes ^PQ3 before ^XZ', () => {
    const template = makeTemplate([makeField()]);
    const result = generateZpl(template, [{}], { quantity: 3 });
    expect(result).toContain('^PQ3');
    expect(result.indexOf('^PQ3')).toBeLessThan(result.lastIndexOf('^XZ'));
  });

  it('2-page template: one record renders both pages as two ^XA...^XZ blocks', () => {
    // pdfme semantics: a single record fills the whole multi-page template.
    const template = makeTemplate([makeField()], 2);
    const result = generateZpl(template, [{}]);
    const xaCount = (result.match(/\^XA/g) || []).length;
    const xzCount = (result.match(/\^XZ/g) || []).length;
    expect(xaCount).toBe(2);
    expect(xzCount).toBe(2);
  });

  it('multi-page values populate every page, not just the first', () => {
    // Regression: per-page indexing left pages after the first blank.
    const template = makeTemplate([makeField()], 3);
    const result = generateZpl(template, [{ field1: 'PRESENT' }]);
    const occurrences = (result.match(/\^FDPRESENT\^FS/g) || []).length;
    expect(occurrences).toBe(3);
  });

  it('uses dpi=203 and quantity=1 by default', () => {
    const template = makeTemplate([makeField()]);
    const result = generateZpl(template, [{}]);
    expect(result).toContain('^PQ1');
  });

  it('empty inputs still produces valid envelope', () => {
    const template = makeTemplate([makeField()]);
    const result = generateZpl(template, []);
    expect(result).toContain('^XA');
    expect(result).toContain('^XZ');
  });
});

// ---------------------------------------------------------------------------
// Coordinate conversion (ZPL-02)
// ---------------------------------------------------------------------------

// We test coordinate conversion indirectly through generateZpl output.
// The plan requires testing mmToDots and ptToDots directly; we expose them
// by verifying known conversions through the output.

describe('Coordinate conversion', () => {
  it('mmToDots(25.4, 203) === 203 — 1 inch at 203 dpi', () => {
    // Field at x=25.4mm, y=0mm: x dots should be 203
    const template = makeTemplate([makeField({ position: { x: 25.4, y: 0 }, type: 'text' })]);
    const result = generateZpl(template, [{ field1: 'v' }], { dpi: 203 });
    expect(result).toContain('^FO203,');
  });

  it('mmToDots(25.4, 300) === 300 — 1 inch at 300 dpi', () => {
    const template = makeTemplate([makeField({ position: { x: 25.4, y: 0 }, type: 'text' })]);
    const result = generateZpl(template, [{ field1: 'v' }], { dpi: 300 });
    expect(result).toContain('^FO300,');
  });

  it('mmToDots(0, 203) === 0', () => {
    const template = makeTemplate([makeField({ position: { x: 0, y: 0 }, type: 'text' })]);
    const result = generateZpl(template, [{ field1: 'v' }], { dpi: 203 });
    expect(result).toContain('^FO0,0');
  });

  it('ptToDots(72, 203) === 203 — 72pt = 1 inch', () => {
    // Font 72pt at 203 dpi should yield fontH=203
    const template = makeTemplate([makeField({ fontSize: 72, type: 'text' })]);
    const result = generateZpl(template, [{ field1: 'v' }], { dpi: 203 });
    expect(result).toContain('^A0N,203,203');
  });

  it('ptToDots(10, 203) === 28 — round(10 * 203/72)', () => {
    const template = makeTemplate([makeField({ fontSize: 10, type: 'text' })]);
    const result = generateZpl(template, [{ field1: 'v' }], { dpi: 203 });
    expect(result).toContain('^A0N,28,28');
  });
});

// ---------------------------------------------------------------------------
// Text field (ZPL-03 text)
// ---------------------------------------------------------------------------

describe('Text field', () => {
  it('produces correct ^FO^A0N^FB^FD^FS for given position/fontSize/width/alignment', () => {
    // x=10 → round(10*203/25.4)=80, y=20 → 160, fontH=round(12*203/72)=34, fieldW=round(50*203/25.4)=400
    const template = makeTemplate([makeField({
      position: { x: 10, y: 20 },
      fontSize: 12,
      width: 50,
      alignment: 'center',
    })]);
    const result = generateZpl(template, [{ field1: 'Hello' }], { dpi: 203 });
    expect(result).toContain('^FO80,160^A0N,34,34^FB400,99,0,C,0^FDHello^FS');
  });

  it('uses default ^FB max_lines=99 so long text wraps without exceeding non-Zebra emulator limits', () => {
    // Brady i6100 and similar emulators silently drop fields when ^FB max_lines
    // is "too high"; 99 is a pragmatic default between wrap headroom and printer quirks.
    const template = makeTemplate([makeField({ fontSize: 12, width: 50, height: 5 })]);
    const result = generateZpl(template, [{ field1: 'x' }], { dpi: 203 });
    expect(result).toMatch(/\^FB\d+,99,0,L,0/);
  });

  it('honours explicit fbMaxLines option (overrides default)', () => {
    const template = makeTemplate([makeField({ fontSize: 12, width: 50 })]);
    const result = generateZpl(template, [{ field1: 'x' }], { dpi: 203, fbMaxLines: 1 });
    expect(result).toMatch(/\^FB\d+,1,0,L,0/);
  });

  it('alignment left uses L in ^FB', () => {
    const template = makeTemplate([makeField({ alignment: 'left' })]);
    const result = generateZpl(template, [{ field1: 'v' }]);
    expect(result).toContain(',L,');
  });

  it('alignment right uses R in ^FB', () => {
    const template = makeTemplate([makeField({ alignment: 'right' })]);
    const result = generateZpl(template, [{ field1: 'v' }]);
    expect(result).toContain(',R,');
  });

  it('no alignment defaults to L', () => {
    const template = makeTemplate([makeField({ alignment: undefined })]);
    const result = generateZpl(template, [{ field1: 'v' }]);
    expect(result).toContain(',L,');
  });

  it('no fontSize defaults to 10pt', () => {
    const template = makeTemplate([makeField({ fontSize: undefined, type: 'text' })]);
    const result = generateZpl(template, [{ field1: 'v' }], { dpi: 203 });
    // ptToDots(10, 203) = round(10*203/72) = 28
    expect(result).toContain('^A0N,28,28');
  });

  it('template_string type treated same as text', () => {
    const template = makeTemplate([makeField({ type: 'template_string', fontSize: 12, alignment: 'left' })]);
    const result = generateZpl(template, [{ field1: 'val' }], { dpi: 203 });
    expect(result).toContain('^A0N');
    expect(result).toContain('^FB');
    expect(result).toContain('^FDval^FS');
  });
});

// ---------------------------------------------------------------------------
// QR code (ZPL-03 qrcode)
// ---------------------------------------------------------------------------

describe('QR code field', () => {
  it('produces ^BQN,2,{mag} with ^FDMA,{value}^FS', () => {
    const template = makeTemplate([makeField({ type: 'qrcode', height: 20 })]);
    const result = generateZpl(template, [{ field1: 'https://example.com' }], { dpi: 203 });
    expect(result).toContain('^BQN,2,');
    expect(result).toContain('^FDMA,https://example.com^FS');
  });

  it('magnification clamped to minimum 1', () => {
    // Very small height → mag should be at least 1
    const template = makeTemplate([makeField({ type: 'qrcode', height: 0.1 })]);
    const result = generateZpl(template, [{ field1: 'x' }], { dpi: 203 });
    expect(result).toMatch(/\^BQN,2,[1-9]\d*/);
  });

  it('magnification clamped to maximum 10', () => {
    // Very large height → mag should not exceed 10
    const template = makeTemplate([makeField({ type: 'qrcode', height: 500 })]);
    const result = generateZpl(template, [{ field1: 'x' }], { dpi: 203 });
    expect(result).toContain('^BQN,2,10');
  });
});

// ---------------------------------------------------------------------------
// Code128 (ZPL-03 code128)
// ---------------------------------------------------------------------------

describe('Code128 field', () => {
  it('produces ^BCN,{h},Y,N,N with correct value', () => {
    const template = makeTemplate([makeField({ type: 'code128', height: 10 })]);
    const result = generateZpl(template, [{ field1: '12345' }], { dpi: 203 });
    // h = round(10 * 203 / 25.4) = 80
    expect(result).toContain('^BCN,80,Y,N,N');
    expect(result).toContain('^FD12345^FS');
  });
});

// ---------------------------------------------------------------------------
// Code39 (ZPL-03 code39)
// ---------------------------------------------------------------------------

describe('Code39 field', () => {
  it('produces ^B3N,N,{h},Y,N with correct value', () => {
    const template = makeTemplate([makeField({ type: 'code39', height: 10 })]);
    const result = generateZpl(template, [{ field1: 'ABC' }], { dpi: 203 });
    expect(result).toContain('^B3N,N,80,Y,N');
    expect(result).toContain('^FDABC^FS');
  });
});

// ---------------------------------------------------------------------------
// EAN-13 (ZPL-03 ean13)
// ---------------------------------------------------------------------------

describe('EAN-13 field', () => {
  it('produces ^BEN,{h},Y,N with correct value', () => {
    const template = makeTemplate([makeField({ type: 'ean13', height: 10 })]);
    const result = generateZpl(template, [{ field1: '590123412345' }], { dpi: 203 });
    expect(result).toContain('^BEN,80,Y,N');
    expect(result).toContain('^FD590123412345^FS');
  });
});

// ---------------------------------------------------------------------------
// GS1 DataMatrix (ZPL-03 gs1datamatrix)
// ---------------------------------------------------------------------------

describe('GS1 DataMatrix field', () => {
  it('produces ^BXN,{h},200 with correct value', () => {
    const template = makeTemplate([makeField({ type: 'gs1datamatrix', height: 8 })]);
    const result = generateZpl(template, [{ field1: '(01)12345678901231' }], { dpi: 203 });
    expect(result).toContain('^BXN,');
    expect(result).toContain(',200');
    expect(result).toContain('^FD(01)12345678901231^FS');
  });
});

// ---------------------------------------------------------------------------
// Plain DataMatrix (freeform text)
// ---------------------------------------------------------------------------

describe('Plain DataMatrix field', () => {
  it('produces ^BXN,{h},200 with freeform text value', () => {
    const template = makeTemplate([makeField({ type: 'datamatrix', height: 8 })]);
    const result = generateZpl(template, [{ field1: 'ESSETI|CS0000123|ABCDEF' }], { dpi: 203 });
    expect(result).toContain('^BXN,');
    expect(result).toContain(',200');
    expect(result).toContain('^FDESSETI|CS0000123|ABCDEF^FS');
  });
});

// ---------------------------------------------------------------------------
// Image rendering (ZPL-04)
// ---------------------------------------------------------------------------

describe('Image field rendering', () => {
  beforeEach(() => {
    vi.spyOn(console, 'warn').mockImplementation(() => {});
  });

  it('pre-computed ^GFA value produces ^FO{x},{y}^GFA,...^FS', () => {
    const gfa = '^GFA,4,4,2,FF00FF00';
    const template = makeTemplate([makeField({ type: 'image', name: 'logo', position: { x: 10, y: 20 } })]);
    // x=10 → round(10*203/25.4) = 80, y=20 → 160
    const result = generateZpl(template, [{ logo: gfa }], { dpi: 203 });
    expect(result).toContain('^FO80,160^GFA,4,4,2,FF00FF00^FS');
  });

  it('linkedImage type also renders with ^GFA value', () => {
    const gfa = '^GFA,2,2,1,FFFF';
    const template = makeTemplate([makeField({ type: 'linkedImage', name: 'pic', position: { x: 5, y: 5 } })]);
    const result = generateZpl(template, [{ pic: gfa }], { dpi: 203 });
    expect(result).toContain('^GFA,2,2,1,FFFF^FS');
  });

  it('empty/falsy image value produces no ZPL output (graceful skip)', () => {
    const template = makeTemplate([makeField({ type: 'image', name: 'img1' })]);
    const result = generateZpl(template, [{ img1: '' }]);
    expect(result).not.toContain('^GFA');
  });

  it('missing image input produces no ZPL output', () => {
    const template = makeTemplate([makeField({ type: 'image', name: 'img1' })]);
    const result = generateZpl(template, [{}]);
    expect(result).not.toContain('^GFA');
  });

  it('unexpected value format (not ^GFA) logs console.warn and produces no output', () => {
    const template = makeTemplate([makeField({ type: 'image', name: 'bad' })]);
    const result = generateZpl(template, [{ bad: 'data:image/png;base64,abc' }]);
    expect(result).not.toContain('data:');
    expect(console.warn).toHaveBeenCalledWith(expect.stringContaining('bad'));
    expect(console.warn).toHaveBeenCalledWith(expect.stringContaining('expected ^GFA'));
  });

  it('unknown field types still skipped with console.warn', () => {
    const template = makeTemplate([makeField({ type: 'unknownCustomType', name: 'unk' })]);
    const result = generateZpl(template, [{}]);
    expect(result).not.toContain('^FD');
    expect(console.warn).toHaveBeenCalledWith(expect.stringContaining('unknownCustomType'));
  });
});

// ---------------------------------------------------------------------------
// Integration
// ---------------------------------------------------------------------------

describe('Integration', () => {
  it('full template with text + barcode + image: all rendered, envelope correct', () => {
    const gfa = '^GFA,4,4,2,FF00FF00';
    const fields = [
      makeField({ name: 'label', type: 'text', position: { x: 5, y: 5 }, fontSize: 10 }),
      makeField({ name: 'barcode', type: 'code128', position: { x: 5, y: 20 }, height: 15 }),
      makeField({ name: 'photo', type: 'image', position: { x: 5, y: 40 } }),
    ];
    const template = makeTemplate(fields);
    const inputs = [{ label: 'Part A', barcode: '9876543210', photo: gfa }];
    const result = generateZpl(template, inputs, { dpi: 203, quantity: 2 });

    expect(result.trim().startsWith('^XA')).toBe(true);
    expect(result.trim().endsWith('^XZ')).toBe(true);
    expect(result).toContain('^PQ2');
    expect(result).toContain('^A0N');           // text field rendered
    expect(result).toContain('^BCN');           // code128 rendered
    expect(result).toContain('^GFA,4,4,2,FF00FF00^FS'); // image field rendered
  });
});
