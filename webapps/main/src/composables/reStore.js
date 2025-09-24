import { DateTime as DT } from 'luxon';
import { onMounted, onUnmounted } from 'vue';

/**
 * Persists a Pinia store state to localStorage
 * @param {Object} store - The Pinia store instance
 * @param {string} storageKey - The localStorage key (defaults to store.$id + '_SESSION')
 * @param {Array} excludeKeys - Array of state keys to exclude from persistence
 */
export function persistStore(store, storageKey = null, excludeKeys = []) {
  const key = storageKey || `${store.$id}_SESSION`;

  // Create a copy of the store state, excluding specified keys
  const stateToSave = { ...store.$state };
  excludeKeys.forEach(key => {
    delete stateToSave[key];
  });

  // Add timestamp for expiration check
  const persistedData = {
    ...stateToSave,
    last_interaction: DT.utc().toMillis()
  };

  window.localStorage.setItem(key, JSON.stringify(persistedData));
}

/**
 * Restores a Pinia store state from localStorage
 * @param {Object} store - The Pinia store instance
 * @param {string} storageKey - The localStorage key (defaults to store.$id + '_SESSION')
 * @param {number} expirationMinutes - Minutes before stored state expires (default: 5)
 * @returns {boolean} - Whether state was successfully restored
 */
export function reStore(store, storageKey = null, expirationMinutes = 5) {
  const key = storageKey || `${store.$id}_SESSION`;
  const persistedState = window.localStorage.getItem(key);

  if (persistedState) {
    try {
      const restored_state = JSON.parse(persistedState);
      const elapsed_milliseconds =
        DT.utc().toMillis() - restored_state.last_interaction;
      const EXPIRATION_MILLISECONDS = expirationMinutes * 60 * 1000;

      if (elapsed_milliseconds < EXPIRATION_MILLISECONDS) {
        // Remove the timestamp before restoring state
        // eslint-disable-next-line no-unused-vars
        const { last_interaction, ...stateWithoutTimestamp } = restored_state;

        // Use Pinia's $patch to update state
        store.$patch(stateWithoutTimestamp);

        window.localStorage.removeItem(key);
        return true;
      }
    } catch (error) {
      console.warn('Failed to restore store state:', error);
    }

    // Clean up expired or invalid data
    window.localStorage.removeItem(key);
  }

  return false;
}

/**
 * Composable to handle store persistence across page refreshes
 * @param {Object|Array} stores - Single store or array of stores to persist
 * @param {Object} options - Configuration options
 * @returns {Object} - Control functions
 */
export function useStorePersistence(stores, options = {}) {
  const {
    excludeKeys = [],
    expirationMinutes = 5,
    storageKey = null
  } = options;

  // Normalize stores to array
  const storeArray = Array.isArray(stores) ? stores : [stores];

  const saveStores = () => {
    storeArray.forEach(store => {
      persistStore(store, storageKey, excludeKeys);
    });
  };

  const restoreStores = () => {
    return storeArray.map(store => {
      return reStore(store, storageKey, expirationMinutes);
    });
  };

  // Set up beforeunload listener
  onMounted(() => {
    // Restore stores on mount
    restoreStores();

    // Save stores before page unload
    window.addEventListener('beforeunload', saveStores);
  });

  onUnmounted(() => {
    // Clean up listener
    window.removeEventListener('beforeunload', saveStores);
  });

  return {
    saveStores,
    restoreStores
  };
}

