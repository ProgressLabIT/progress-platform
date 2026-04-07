/**
 * formulaWidget.js
 *
 * Custom pdfme prop-panel widget for computed/template-expression formula fields.
 * Renders a syntax-highlighted, auto-growing textarea using a transparent overlay
 * on top of a Prism-highlighted <pre> element — no framework dependencies.
 *
 * Token types highlighted:
 *   token-ref   — {{...}} references (preset, cf::, field::)
 *   function    — built-in function names (IF, CONCAT, ROUND, …)
 *   string      — double-quoted string literals
 *   number      — numeric literals
 *   operator    — arithmetic and comparison operators
 *   punctuation — parentheses and commas
 */

import Prism from 'prismjs';

// ---------------------------------------------------------------------------
// Prism language grammar for the formula DSL
// ---------------------------------------------------------------------------

Prism.languages.formula = {
  'token-ref': {
    pattern: /\{\{[\w:.]+(?:\s+[\w:.]+)*\}\}/,
    greedy: false,
  },
  'function': {
    pattern: /\b(?:IF|CONCAT|UPPER|LOWER|ROUND|ABS|CEIL|FLOOR|FORMAT_DATE|DAYS_BETWEEN|DATE_ADD|YEAR|MONTH|DAY|WEEK|SPLIT|NOW|DATE)\b/,
  },
  'string': {
    pattern: /"(?:\\[\s\S]|[^"\\])*"/,
    greedy: true,
  },
  'number': /\b\d+(?:\.\d+)?\b/,
  'operator': /==|!=|<=|>=|[+\-*/<>]/,
  'punctuation': /[(),]/,
};

// ---------------------------------------------------------------------------
// Theme helpers
// ---------------------------------------------------------------------------

/**
 * Build a CSS string for the syntax-color custom properties from the pdfme theme token.
 * Falls back to reasonable defaults when a color is absent.
 */
function buildTokenColors(theme) {
  return `
    --fe-color-token-ref:  ${theme?.colorPrimary   ?? '#22AED1'};
    --fe-color-function:   ${theme?.colorWarning    ?? '#FF9F1C'};
    --fe-color-string:     ${theme?.colorSuccess    ?? '#0DAB76'};
    --fe-color-number:     #b5cea8;
    --fe-color-operator:   ${theme?.colorError      ?? '#E71D36'};
    --fe-color-punctuation:${theme?.colorTextSecondary ?? 'rgba(255,255,255,0.45)'};
  `;
}

// ---------------------------------------------------------------------------
// Widget
// ---------------------------------------------------------------------------

const MIN_HEIGHT = 120;
const FONT = "13px/1.5 'JetBrains Mono', 'Fira Mono', 'Cascadia Code', Consolas, 'Courier New', monospace";
const PADDING = '8px 10px';

/**
 * pdfme prop-panel custom widget for formula expression fields.
 *
 * @param {import('@pdfme/common').PropPanelWidgetProps} props
 */
export function formulaEditorWidget(props) {
  const { rootElement, value, onChange, schema, theme } = props;

  rootElement.innerHTML = '';
  rootElement.style.width = '100%';

  // ---- wrapper ----
  const wrapper = document.createElement('div');
  wrapper.style.cssText = `
    position: relative;
    width: 100%;
    box-sizing: border-box;
    min-height: ${MIN_HEIGHT}px;
    border: 1px solid ${theme?.colorBorder ?? 'rgba(255,255,255,0.2)'};
    border-radius: 6px;
    overflow: hidden;
    background: ${theme?.colorBgContainer ?? 'transparent'};
  `;

  // ---- highlight layer (<pre>) ----
  const pre = document.createElement('pre');
  pre.setAttribute('aria-hidden', 'true');
  pre.style.cssText = `
    position: absolute;
    inset: 0;
    margin: 0;
    padding: ${PADDING};
    font: ${FONT};
    white-space: pre-wrap;
    word-wrap: break-word;
    overflow: hidden;
    pointer-events: none;
    color: transparent;
    ${buildTokenColors(theme)}
  `;

  const code = document.createElement('code');
  pre.appendChild(code);

  // ---- editable textarea ----
  const focusBorderColor = theme?.colorPrimary ?? '#22AED1';
  const textarea = document.createElement('textarea');
  textarea.value = value ?? '';
  textarea.placeholder = schema?.props?.placeholder ?? '';
  textarea.spellcheck = false;
  textarea.style.cssText = `
    display: block;
    position: relative;
    width: 100%;
    min-height: ${MIN_HEIGHT}px;
    height: ${MIN_HEIGHT}px;
    padding: ${PADDING};
    margin: 0;
    font: ${FONT};
    color: ${theme?.colorText ?? 'inherit'};
    background: transparent;
    border: none;
    outline: none;
    resize: vertical;
    white-space: pre-wrap;
    word-wrap: break-word;
    overflow: auto;
    caret-color: ${theme?.colorText ?? 'inherit'};
    box-sizing: border-box;
  `;

  textarea.addEventListener('focus', () => {
    wrapper.style.borderColor = focusBorderColor;
    wrapper.style.boxShadow = `0 0 0 1px ${focusBorderColor}`;
  });
  textarea.addEventListener('blur', () => {
    wrapper.style.borderColor = theme?.colorBorder ?? 'rgba(255,255,255,0.2)';
    wrapper.style.boxShadow = 'none';
  });

  // ---- inline styles for Prism token classes ----
  const styleTag = document.createElement('style');
  styleTag.textContent = `
    .formula-editor pre .token.token-ref   { color: var(--fe-color-token-ref); }
    .formula-editor pre .token.function    { color: var(--fe-color-function); font-weight: 600; }
    .formula-editor pre .token.string      { color: var(--fe-color-string); }
    .formula-editor pre .token.number      { color: var(--fe-color-number); }
    .formula-editor pre .token.operator    { color: var(--fe-color-operator); }
    .formula-editor pre .token.punctuation { color: var(--fe-color-punctuation); }
  `;
  wrapper.classList.add('formula-editor');

  // ---- highlight update ----
  function updateHighlight(text) {
    code.innerHTML = Prism.highlight(text, Prism.languages.formula, 'formula')
      // Prism escapes & < > in plain text — mirror that in the textarea model
      + '\n'; // trailing newline prevents last-line collapse
  }

  // ---- auto-grow ----
  function autoGrow() {
    textarea.style.height = 'auto';
    const next = Math.max(MIN_HEIGHT, textarea.scrollHeight);
    textarea.style.height = next + 'px';
    pre.style.height = next + 'px';
  }

  // ---- scroll sync ----
  function syncScroll() {
    pre.scrollTop = textarea.scrollTop;
    pre.scrollLeft = textarea.scrollLeft;
  }

  // ---- event wiring via AbortController for clean teardown ----
  const ac = new AbortController();
  const opts = { signal: ac.signal };

  // Stop keyboard events from bubbling to the Designer (which would delete the field on Backspace/Delete)
  textarea.addEventListener('keydown', (e) => e.stopPropagation(), opts);
  textarea.addEventListener('keyup', (e) => e.stopPropagation(), opts);
  textarea.addEventListener('keypress', (e) => e.stopPropagation(), opts);

  // Update highlighting locally on every keystroke (pure DOM, no form-render round-trip).
  // Commit the value to form-render only on blur — calling onChange on every input
  // would cause WidgetRenderer to destroy + re-create the widget, losing focus.
  textarea.addEventListener('input', () => {
    updateHighlight(textarea.value);
    autoGrow();
  }, opts);

  textarea.addEventListener('blur', () => {
    onChange?.(textarea.value);
  }, opts);

  textarea.addEventListener('scroll', syncScroll, opts);

  // pdfme wipes rootElement.innerHTML on re-render; abort listeners then
  const mo = new MutationObserver(() => {
    if (!rootElement.contains(wrapper)) {
      ac.abort();
      mo.disconnect();
    }
  });
  mo.observe(rootElement, { childList: true });

  // ---- initial render ----
  updateHighlight(textarea.value);
  wrapper.appendChild(styleTag);
  wrapper.appendChild(pre);
  wrapper.appendChild(textarea);
  rootElement.appendChild(wrapper);

  // run auto-grow after paint so scrollHeight is accurate
  requestAnimationFrame(autoGrow);
}
