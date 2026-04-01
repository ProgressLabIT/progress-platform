import { Notify } from 'quasar';
import { useSSE } from '@/composables/useSSE';
import { useListsStore } from 'app/src/stores/lists';

const RELEVANT = ['WAREHOUSE_LIST_CREATED', 'WAREHOUSE_LIST_CLOSED'];

/**
 * Subscribe to inventory SSE and refresh open movement lists when list lifecycle events fire.
 * Mirrors main app MovementListsRoot.vue handling (topic `inventory`).
 *
 * @param {string} listType - API `type` for /movement-list (e.g. 'shipment', 'receipt')
 */
export function useWarehouseMovementListEvents(listType) {
  const lists = useListsStore();
  const { subscribe } = useSSE('inventory');

  subscribe((message) => {
    let event;
    try {
      event = JSON.parse(message.data);
    } catch {
      return;
    }
    if (event.notification === 'ERROR') {
      Notify.create({
        position: 'top',
        message: typeof event.error === 'string' ? event.error : (event.error_code || 'Error'),
        color: 'theme-red',
        timeout: 1500,
      });
      return;
    }
    const t = event.event_type || event.notification;
    if (!t || RELEVANT.includes(t)) {
      lists.refreshHeaders(listType);
    }
  });
}
