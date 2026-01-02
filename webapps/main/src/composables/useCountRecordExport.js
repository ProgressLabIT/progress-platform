/**
 * Composable for exporting count session records to CSV/XLSX
 *
 * Exports all session records at the most granular level (exploding serials to individual rows).
 * Removed serials (in system but not counted) are exported with counted_qt=0.
 */

import { ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { Notify } from 'quasar';
import { api } from '@/boot/axios.js';
import { XLSXDownload } from '@/lib/xlsxDownload.js';
import { saveAs } from 'file-saver';

export function useCountRecordExport() {
  const { t } = useI18n();
  const exporting = ref(false);

  /**
   * Fetch all records for a session (bypassing UI filters)
   * @param {string} sessionKey - Count session key
   * @returns {Promise<Array>} Raw records from API
   */
  async function fetchAllRecords(sessionKey) {
    const { data } = await api.get('/inventory/count-record', {
      params: {
        count_session_key: sessionKey,
        include_started: false,
        include_completed: true,
        include_discarded: false,
        limit: null, // No limit - get all records
      },
    });
    return data;
  }

  /**
   * Explode records to individual rows for export
   * - Non-serialized: one row per record
   * - Serialized: one row per serial (counted=1 or removed=0)
   *
   * @param {Array} records - Raw records from API
   * @param {Function} getUserName - Function to get user name from key
   * @returns {Array} Flat rows for export
   */
  function explodeRecordsToRows(records, getUserName) {
    const rows = [];

    for (const record of records) {
      const baseRow = {
        position_code: record.position_code,
        product_code: record.product_code,
        user: getUserName(record.user_key),
        counted_at: record.counted_at ? new Date(record.counted_at).toISOString() : '',
      };

      // Check if this is a serialized record
      const hasSerials = (record.system_serials?.length > 0) || (record.counted_serials?.length > 0);

      if (!hasSerials) {
        // Non-serialized: single row with quantities
        rows.push({
          ...baseRow,
          serial_code: '',
          system_qt: record.system_qt ?? 0,
          counted_qt: record.counted_qt ?? 0,
          delta: (record.counted_qt ?? 0) - (record.system_qt ?? 0),
        });
      } else {
        // Serialized: explode to individual rows
        const systemSerialCodes = new Set(
          (record.system_serials || []).map(s => s.serial_code)
        );
        const countedSerialCodes = new Set(
          (record.counted_serials || []).map(s => s.serial_code)
        );

        // All unique serials (union of system and counted)
        const allSerialCodes = new Set([...systemSerialCodes, ...countedSerialCodes]);

        for (const serialCode of allSerialCodes) {
          const inSystem = systemSerialCodes.has(serialCode);
          const inCounted = countedSerialCodes.has(serialCode);

          rows.push({
            ...baseRow,
            serial_code: serialCode,
            system_qt: inSystem ? 1 : 0,
            counted_qt: inCounted ? 1 : 0,
            delta: (inCounted ? 1 : 0) - (inSystem ? 1 : 0),
          });
        }
      }
    }

    return rows;
  }

  /**
   * Export records to XLSX format
   * @param {string} sessionKey - Count session key
   * @param {string} sessionCode - Session code for filename
   * @param {Function} getUserName - Function to get user name from key
   */
  async function exportToXLSX(sessionKey, sessionCode, getUserName) {
    exporting.value = true;
    try {
      const records = await fetchAllRecords(sessionKey);

      if (records.length === 0) {
        Notify.create({
          message: t('warehouse.counting.export_no_records'),
          color: 'warning',
          position: 'top',
        });
        return;
      }

      const rows = explodeRecordsToRows(records, getUserName);

      // Format data for XLSX
      const exportData = rows.map(row => ({
        [t('warehouse.counting.export_col_position')]: row.position_code,
        [t('warehouse.counting.export_col_product')]: row.product_code,
        [t('warehouse.counting.export_col_serial')]: row.serial_code,
        [t('warehouse.counting.export_col_system_qt')]: row.system_qt,
        [t('warehouse.counting.export_col_counted_qt')]: row.counted_qt,
        [t('warehouse.counting.export_col_delta')]: row.delta,
        [t('warehouse.counting.export_col_username')]: row.username,
        [t('warehouse.counting.export_col_counted_at')]: row.counted_at,
      }));

      const filename = `count_session_${sessionCode}_${new Date().toISOString().slice(0, 10)}`;
      XLSXDownload(exportData, 'Count Records', filename);

      Notify.create({
        message: t('warehouse.counting.export_success', { count: rows.length }),
        color: 'positive',
        position: 'top',
      });
    } catch (error) {
      console.error('Export failed:', error);
      Notify.create({
        message: t('warehouse.counting.export_error'),
        color: 'negative',
        position: 'top',
      });
    } finally {
      exporting.value = false;
    }
  }

  /**
   * Export records to CSV format
   * @param {string} sessionKey - Count session key
   * @param {string} sessionCode - Session code for filename
   * @param {Function} getUserName - Function to get user name from key
   */
  async function exportToCSV(sessionKey, sessionCode, getUserName) {
    exporting.value = true;
    try {
      const records = await fetchAllRecords(sessionKey);

      if (records.length === 0) {
        Notify.create({
          message: t('warehouse.counting.export_no_records'),
          color: 'warning',
          position: 'top',
        });
        return;
      }

      const rows = explodeRecordsToRows(records, getUserName);

      // Build CSV content
      const headers = [
        'position_code',
        'product_code',
        'serial_code',
        'system_qt',
        'counted_qt',
        'delta',
        'user',
        'counted_at',
      ];

      const csvLines = [headers.join(',')];
      for (const row of rows) {
        const values = headers.map(h => {
          const val = row[h] ?? '';
          // Escape quotes and wrap in quotes if contains comma or quote
          const strVal = String(val);
          if (strVal.includes(',') || strVal.includes('"') || strVal.includes('\n')) {
            return `"${strVal.replace(/"/g, '""')}"`;
          }
          return strVal;
        });
        csvLines.push(values.join(','));
      }

      const csvContent = csvLines.join('\n');
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8' });
      const filename = `count_session_${sessionCode}_${new Date().toISOString().slice(0, 10)}.csv`;
      saveAs(blob, filename);

      Notify.create({
        message: t('warehouse.counting.export_success', { count: rows.length }),
        color: 'positive',
        position: 'top',
      });
    } catch (error) {
      console.error('Export failed:', error);
      Notify.create({
        message: t('warehouse.counting.export_error'),
        color: 'negative',
        position: 'top',
      });
    } finally {
      exporting.value = false;
    }
  }

  return {
    exporting,
    exportToXLSX,
    exportToCSV,
  };
}



