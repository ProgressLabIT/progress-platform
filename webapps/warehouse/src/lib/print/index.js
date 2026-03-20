import { Notify } from 'quasar';
import { i18n } from 'boot/i18n';
import { api } from 'src/boot/axios';
import { generateZpl } from './zpl.js';
import { resolveExpression } from './templateResolver.js';
import { useConfigStore } from '@/stores/config';
import store from '@/store/index.js';

const { t: $t } = i18n.global;

/**
 * Normalize a pdfme page schema to a flat array of field objects.
 */
function normalizePageSchema(pageSchema) {
  if (!pageSchema) return [];
  if (Array.isArray(pageSchema)) return pageSchema;
  return Object.entries(pageSchema).map(([fieldName, fieldSpec]) => ({ ...fieldSpec, name: fieldName }));
}

/**
 * Build a minimal context object for warehouse preset resolution.
 * Implements getPresetValue and getCustomFieldValue matching the interface
 * expected by resolveExpression().
 */
function buildProductContext(product) {
  return {
    getPresetValue(key) {
      if (key === 'product.code') return product.code;
      if (key === 'product.description') return product.description;
      return undefined;
    },
    getCustomFieldValue() { return undefined; },
  };
}

function buildPositionContext(positionCode) {
  return {
    getPresetValue(key) {
      if (key === 'position.code') return positionCode;
      return undefined;
    },
    getCustomFieldValue() { return undefined; },
  };
}

/**
 * Resolve all fields of a template against a context object.
 * Returns inputs array suitable for generateZpl().
 */
function resolveTemplateInputs(templateData, context) {
  const schemas = templateData.template?.schemas || [];
  return schemas.map(pageSchema => {
    const fields = normalizePageSchema(pageSchema);
    return Object.fromEntries(
      fields.map(field => {
        let value = '';
        if (field.linkType === 'preset' && field.linkValue) {
          value = context.getPresetValue(field.linkValue) ?? '';
        } else if (field.linkType === 'template_expression' && field.templateExpression) {
          value = resolveExpression(field.templateExpression, context, []) ?? '';
        }
        return [field.name, String(value)];
      })
    );
  });
}

/**
 * Get the user's configured printer from preferences.
 * Returns a printer object from config.printers or null.
 */
function getUserPrinter() {
  const { config } = useConfigStore();
  const prefValue = store?.state?.session?.user?.preferences?.printer ?? null;
  if (!prefValue) return null;
  return config.printers?.find(p => `${p.host}:${p.port}` === prefValue) ?? null;
}

/**
 * Fetch a print template by key from the API.
 */
async function fetchTemplate(templateKey) {
  if (!templateKey) return null;
  const { data } = await api.get(`print-template/${templateKey}`);
  return data;
}

/**
 * Submit a print job to the main API.
 */
async function submitPrintJob(zplData, printer) {
  const payload = {
    printer_host: printer.host,
    printer_port: printer.port,
    format: 'zpl',
    data: zplData,
    copies: 1,
    timeout_seconds: printer.timeout_seconds ?? 5,
  };
  return api.post('print-job', payload);
}

/**
 * Wait for the SSE print-result event for a given job_id.
 * Resolves with { ok, error, detail } when the result arrives or on timeout.
 */
function waitForPrintResult(jobId, timeoutMs) {
  return new Promise((resolve) => {
    const url = api.defaults.baseURL + '/notification/print-result';
    const source = new EventSource(url, { withCredentials: false });
    const timer = setTimeout(() => {
      source.close();
      resolve({ ok: false, error: 'timeout', detail: null });
    }, timeoutMs);
    source.addEventListener('print-result', (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.job_id === jobId) {
          clearTimeout(timer);
          source.close();
          resolve({ ok: data.ok, error: data.error ?? null, detail: data.detail ?? null });
        }
      } catch (e) { /* ignore */ }
    });
    source.onerror = () => {};
  });
}

/**
 * Print a product label using the configured product label template.
 * Preserves the same function signature as the original for backward compatibility.
 * @param {string} productCode
 * @param {string} productDescription
 */
export async function printProductLabel(productCode, productDescription) {
  try {
    const { config } = useConfigStore();
    const templateKey = config.productLabelTemplate;
    if (!templateKey) {
      Notify.create({ color: 'theme-red', message: $t('alerts.no_template_configured') || 'No product label template configured' });
      return;
    }

    const printer = getUserPrinter();
    if (!printer) {
      Notify.create({ color: 'theme-red', message: $t('alerts.no_printer_found') });
      return;
    }

    const templateData = await fetchTemplate(templateKey);
    if (!templateData) {
      Notify.create({ color: 'theme-red', message: 'Failed to load print template' });
      return;
    }

    const context = buildProductContext({ code: productCode, description: productDescription });
    const inputs = resolveTemplateInputs(templateData, context);
    const zpl = generateZpl(templateData.template, inputs, { dpi: 203, quantity: 1 });

    const { data: responseData } = await submitPrintJob(zpl, printer);
    const timeoutMs = ((printer.timeout_seconds ?? 5) + 5) * 1000;
    const result = await waitForPrintResult(responseData.job_id, timeoutMs);
    if (result.ok) {
      Notify.create({ color: 'theme-green', message: $t('alerts.print_job_sent') || 'Label sent to printer' });
    } else if (result.error === 'timeout') {
      Notify.create({ color: 'theme-orange', message: $t('alerts.print_timeout') || 'Printer did not respond in time' });
    } else {
      Notify.create({ color: 'theme-red', message: result.detail || $t('alerts.print_failed') || 'Print failed' });
    }
  } catch (error) {
    console.error('printProductLabel error:', error);
    Notify.create({ color: 'theme-red', message: error.message || 'Print failed' });
  }
}

/**
 * Print a position label using the configured position label template.
 * Preserves the same function signature as the original for backward compatibility.
 * @param {string} position - The position code
 */
export async function printPositionLabel(position) {
  try {
    const { config } = useConfigStore();
    const templateKey = config.positionLabelTemplate;
    if (!templateKey) {
      Notify.create({ color: 'theme-red', message: $t('alerts.no_template_configured') || 'No position label template configured' });
      return;
    }

    const printer = getUserPrinter();
    if (!printer) {
      Notify.create({ color: 'theme-red', message: $t('alerts.no_printer_found') });
      return;
    }

    const templateData = await fetchTemplate(templateKey);
    if (!templateData) {
      Notify.create({ color: 'theme-red', message: 'Failed to load print template' });
      return;
    }

    const positionCode = typeof position === 'object' ? position.code : position;
    const context = buildPositionContext(positionCode);
    const inputs = resolveTemplateInputs(templateData, context);
    const zpl = generateZpl(templateData.template, inputs, { dpi: 203, quantity: 1 });

    const { data: responseData } = await submitPrintJob(zpl, printer);
    const timeoutMs = ((printer.timeout_seconds ?? 5) + 5) * 1000;
    const result = await waitForPrintResult(responseData.job_id, timeoutMs);
    if (result.ok) {
      Notify.create({ color: 'theme-green', message: $t('alerts.print_job_sent') || 'Label sent to printer' });
    } else if (result.error === 'timeout') {
      Notify.create({ color: 'theme-orange', message: $t('alerts.print_timeout') || 'Printer did not respond in time' });
    } else {
      Notify.create({ color: 'theme-red', message: result.detail || $t('alerts.print_failed') || 'Print failed' });
    }
  } catch (error) {
    console.error('printPositionLabel error:', error);
    Notify.create({ color: 'theme-red', message: error.message || 'Print failed' });
  }
}
