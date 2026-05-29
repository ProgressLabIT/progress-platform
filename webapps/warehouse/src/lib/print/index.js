import { Notify } from 'quasar';
import { i18n } from 'boot/i18n';
import { api } from 'src/boot/axios';
import { generateZpl } from './zpl.js';
import { processZplImageFields } from './zplImage.js';
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

function schemasToV5(schemas) {
  if (!schemas || !Array.isArray(schemas)) return [];
  return schemas.map(normalizePageSchema);
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
 * Returns inputs array suitable for generateZpl(): a single merged record
 * holding every field across all pages (pdfme record semantics — one record
 * renders the whole multi-page template). Field names are unique template-wide.
 */
function resolveTemplateInputs(templateData, context) {
  const schemas = templateData.template?.schemas || [];
  const record = {};
  for (const pageSchema of schemas) {
    for (const field of normalizePageSchema(pageSchema)) {
      if (!field.name) continue;
      let value = '';
      if (field.linkType === 'preset' && field.linkValue) {
        value = context.getPresetValue(field.linkValue) ?? '';
      } else if (field.linkType === 'template_expression' && field.templateExpression) {
        value = resolveExpression(field.templateExpression, context, []) ?? '';
      } else if (!field.linkType || field.linkType === 'none') {
        value = field.content ?? '';
      }
      record[field.name] = String(value);
    }
  }
  return [record];
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
 * Submit a print job to the API via NATS req/reply.
 * The API forwards the request to the print-service over NATS and returns
 * the result synchronously in the HTTP response.
 */
async function submitPrintJob(zplData, printer) {
  const payload = {
    printer_host: printer.host,
    printer_port: printer.port,
    format: 'zpl',
    data: zplData,
    copies: 1,
    timeout_seconds: printer.timeout_seconds ?? 5,
    printer_key: printer.name ?? `${printer.host}:${printer.port}`,
  };
  const response = await api.post('print-job', payload);
  return response.data;
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

    const dpi = printer.dpi || 203;
    const offsetX = printer.offset_x || 0;
    const offsetY = printer.offset_y || 0;
    const context = buildProductContext({ code: productCode, description: productDescription });
    const inputs = resolveTemplateInputs(templateData, context);
    const zplInputs = await processZplImageFields(
      schemasToV5(templateData.template?.schemas),
      inputs,
      dpi,
    );
    const zpl = generateZpl(templateData.template, zplInputs, { dpi, quantity: 1, offsetX, offsetY });

    const result = await submitPrintJob(zpl, printer);
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

    const dpi = printer.dpi || 203;
    const offsetX = printer.offset_x || 0;
    const offsetY = printer.offset_y || 0;
    const positionCode = typeof position === 'object' ? position.code : position;
    const context = buildPositionContext(positionCode);
    const inputs = resolveTemplateInputs(templateData, context);
    const zplInputs = await processZplImageFields(
      schemasToV5(templateData.template?.schemas),
      inputs,
      dpi,
    );
    const zpl = generateZpl(templateData.template, zplInputs, { dpi, quantity: 1, offsetX, offsetY });

    const result = await submitPrintJob(zpl, printer);
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
