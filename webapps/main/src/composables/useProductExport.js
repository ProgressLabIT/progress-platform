import { ref } from 'vue';
import { api } from '@/boot/axios';

export function useProductExport() {
  const exporting = ref(false);

  async function exportProducts(filters, format = 'xlsx') {
    exporting.value = true;
    try {
      // Export = ALL rows matching the active filters. limit/offset are the
      // list view's pagination window (ProductList passes load_quantity/offset
      // in `filters`); they must not constrain the export, so strip them here.
      // The backend also nulls them, but stripping client-side keeps the export
      // correct regardless of which API build is serving the request.
      const exportFilters = { ...(filters || {}) };
      delete exportFilters.limit;
      delete exportFilters.offset;
      const resp = await api.get('/product/export', {
        params: { ...exportFilters, format },
        responseType: 'arraybuffer',
      });
      const contentType =
        resp.headers['content-type'] || 'application/octet-stream';
      const blob = new Blob([resp.data], { type: contentType });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      const ext = format === 'csv' ? 'csv' : 'xlsx';
      if (format === 'template') {
        link.download = `products_template.${ext}`;
      } else {
        // Local time, filesystem-safe (no colons): YYYY-MM-DD_HH-MM-SS
        const d = new Date();
        const p = (n) => String(n).padStart(2, '0');
        const ts = `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}_${p(d.getHours())}-${p(d.getMinutes())}-${p(d.getSeconds())}`;
        link.download = `products_${ts}.${ext}`;
      }
      link.click();
      window.URL.revokeObjectURL(url);
    } finally {
      exporting.value = false;
    }
  }

  return { exporting, exportProducts };
}
