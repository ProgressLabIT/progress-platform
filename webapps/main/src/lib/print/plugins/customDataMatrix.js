/**
 * Plain DataMatrix plugin for pdfme.
 *
 * Unlike gs1datamatrix (which enforces strict GS1 AI format), this plugin
 * encodes arbitrary text into a standard DataMatrix barcode via bwip-js
 * with bcid "datamatrix".
 */
import bwipjs from 'bwip-js';
import { b64toUint8Array, mm2pt } from '@pdfme/common';
import { createLinkSchema, linkDefaults } from './linkConfig.js';
import { formulaEditorWidget } from './formulaWidget.js';

const DEFAULT_BG = '#ffffff';
const DEFAULT_BAR = '#000000';

function stripHash(hex) {
  return hex ? hex.replace('#', '') : '000000';
}

function renderToCanvas(value, schema) {
  const canvas = document.createElement('canvas');
  const opts = {
    bcid: 'datamatrix',
    text: value,
    scale: 5,
    width: schema.width,
    height: schema.height,
  };
  if (schema.backgroundColor) opts.backgroundcolor = stripHash(schema.backgroundColor);
  if (schema.barColor) opts.barcolor = stripHash(schema.barColor);
  bwipjs.toCanvas(canvas, opts);
  return canvas;
}

function canvasToPngBytes(canvas) {
  const dataUrl = canvas.toDataURL('image/png');
  return b64toUint8Array(dataUrl);
}

const dataMatrixIcon =
  '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24">' +
  '<path fill="currentColor" d="M2 2H6V4H4V6H2V2M8 2H10V4H8V2M20 2V4H22V6H20V8H22V10H20V12H22V14H20V16H22V20H20V18H18V20H14V18H16V16H14V18H12V20H10V18H8V16H10V14H12V12H10V14H8V12H6V14H4V12H6V10H4V8H2V20H4V22H2V24H6V22H8V24H10V22H12V24H14V22H16V24H22V22H20V20H22V16H20V14H18V16H16V14H14V16H12V14H14V12H16V14H18V12H16V10H18V8H16V6H18V4H16V2H20M14 2V4H12V2H14M12 4H14V6H12V4M6 6V8H8V10H6V12H4V10H2V8H4V6H6M10 6V8H8V6H10M12 6H14V8H12V6M16 8V10H14V8H16M6 10H8V12H6V10M10 10V12H12V10H10M16 10H18V12H16V10M4 14H6V16H4V14M10 16V18H8V16H10M12 16H14V18H12V16M16 16H18V18H16V16"/>' +
  '</svg>';

/**
 * @param {Array<{ _key: string; name?: string; default_label?: string }>} [customFields]
 * @returns {import('@pdfme/common').Plugin}
 */
export function createDataMatrixPlugin(customFields = []) {
  return {
    pdf: async (arg) => {
      const { value, schema, pdfDoc, page, _cache } = arg;
      if (!value) return;

      const cacheKey = `datamatrix|${schema.backgroundColor}|${schema.barColor}|${value}`;
      let image = _cache.get(cacheKey);
      if (!image) {
        const pngBytes = canvasToPngBytes(renderToCanvas(value, schema));
        image = await pdfDoc.embedPng(pngBytes);
        _cache.set(cacheKey, image);
      }

      const pageHeight = page.getHeight();
      const rotateDeg = schema.rotate ? -schema.rotate : 0;
      const w = mm2pt(schema.width);
      const h = mm2pt(schema.height);
      let x = mm2pt(schema.position.x);
      let y = pageHeight - mm2pt(schema.position.y) - h;

      if (rotateDeg) {
        const cx = x + w / 2;
        const cy = pageHeight - mm2pt(schema.position.y) - h / 2;
        const rad = (rotateDeg * Math.PI) / 180;
        const cos = Math.cos(rad);
        const sin = Math.sin(rad);
        const dx = x - cx;
        const dy = y - cy;
        x = cos * dx - sin * dy + cx;
        y = sin * dx + cos * dy + cy;
      }

      const { degrees } = await import('@pdfme/pdf-lib');
      page.drawImage(image, {
        x,
        y,
        width: w,
        height: h,
        rotate: degrees(rotateDeg),
        opacity: schema.opacity,
      });
    },

    ui: async (arg) => {
      const { value, rootElement, mode, onChange, stopEditing, tabIndex, placeholder, schema } = arg;
      const container = document.createElement('div');
      Object.assign(container.style, {
        width: '100%',
        height: '100%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      });
      rootElement.appendChild(container);

      const editable = mode === 'designer' || mode === 'form';
      if (editable) {
        const input = document.createElement('input');
        Object.assign(input.style, {
          width: '100%',
          position: 'absolute',
          textAlign: 'center',
          fontSize: '12pt',
          fontWeight: 'bold',
          color: '#fff',
          backgroundColor: 'rgba(0,0,0,0.5)',
          border: 'none',
        });
        input.value = value;
        input.placeholder = placeholder || '';
        input.tabIndex = tabIndex || 0;
        input.addEventListener('change', (e) => {
          if (onChange) onChange({ key: 'content', value: e.target.value });
        });
        input.addEventListener('blur', () => {
          if (stopEditing) stopEditing();
        });
        container.appendChild(input);
        if (mode === 'designer') input.focus();
      }

      if (!value) return;
      try {
        const canvas = renderToCanvas(value, schema);
        const blob = await new Promise((res) => canvas.toBlob(res, 'image/png'));
        const url = URL.createObjectURL(blob);
        const img = document.createElement('img');
        img.src = url;
        Object.assign(img.style, { width: '100%', height: '100%', borderRadius: '0' });
        container.appendChild(img);
      } catch (err) {
        console.error('DataMatrix render error:', err);
        const errEl = document.createElement('div');
        errEl.textContent = '⚠';
        errEl.style.color = 'red';
        container.appendChild(errEl);
      }
    },

    icon: dataMatrixIcon,

    propPanel: {
      widgets: { FormulaEditor: formulaEditorWidget },
      schema: (props) => ({
        ...createLinkSchema(customFields, props.activeSchema),
        barColor: {
          title: 'Bar Color',
          type: 'string',
          widget: 'color',
          props: { disabledAlpha: true },
          rules: [{ pattern: '^#[0-9a-fA-F]{6}$', message: 'Invalid hex color' }],
        },
        backgroundColor: {
          title: 'Background Color',
          type: 'string',
          widget: 'color',
          props: { disabledAlpha: true },
          rules: [{ pattern: '^#[0-9a-fA-F]{6}$', message: 'Invalid hex color' }],
        },
      }),
      defaultSchema: {
        name: '',
        type: 'datamatrix',
        content: 'Hello DataMatrix',
        position: { x: 0, y: 0 },
        width: 30,
        height: 30,
        rotate: 0,
        opacity: 1,
        backgroundColor: DEFAULT_BG,
        barColor: DEFAULT_BAR,
        ...linkDefaults,
      },
    },
  };
}
