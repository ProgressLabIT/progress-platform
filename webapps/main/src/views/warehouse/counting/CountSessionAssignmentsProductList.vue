<template>
  <div class="fit col">
    <q-virtual-scroll
      v-if="!isLoading"
      v-slot="{ item }"
      style="max-height: 100%"
      class="col fit"
      :items="filteredItems"
    >
      <q-item
        :key="item._key"
        clickable
        style="min-height: none"
        :disable="disableItem(item)"
        @click="toggleItem(item)"
      >
        <q-item-section side>
          <q-checkbox
            size="sm"
            dense
            :model-value="isItemSelected(item)"
            @click="toggleItem(item)"
          />
        </q-item-section>
        <q-item-section>
          <q-item-label class="highlight">
            {{ item.code }}
          </q-item-label>
          <q-item-label caption class="ellipsis">
            {{ item.description }}
          </q-item-label>
        </q-item-section>
        <q-item-section v-if="getItemAssignees(item).length > 0" side>
          <template v-if="getItemAssignees(item).length === 1">
            <BaseUserAvatar
              :user="getItemAssignees(item)[0]"
              :show_name="false"
              size="32px"
              dense
            />
          </template>
          <template v-else>
            <div class="row items-center q-gutter-x-xs">
              <q-icon
                name="mdi-account-group"
                size="20px"
              >
                <q-tooltip>
                  <div v-for="user in getItemAssignees(item)" :key="user._key">
                    {{ user.name }} {{ user.surname }}
                  </div>
                </q-tooltip>
              </q-icon>
              <span class="text-caption">{{ getItemAssignees(item).length }}</span>
            </div>
          </template>
        </q-item-section>
      </q-item>
    </q-virtual-scroll>
  </div>
</template>

<script setup>
import { computed, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { Notify } from 'quasar';
import BaseUserAvatar from '@/components/BaseUserAvatar.vue';
import { useWildcardToRegex } from '@/composables/useWildcardToRegex';
import { useCountSessionStore } from '@/stores/countSession';
import { useStore } from 'vuex';

const props = defineProps({
  items: {
    type: Array,
    required: true,
  },
  assignments: {
    type: Array,
    default: () => [],
  },
  disableAssignedItems: {
    type: Boolean,
    default: false,
  },
  searchText: {
    type: String,
    default: '',
  },
  showMultiAssignedOnly: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(['update:stats']);
const selectedAssignment = defineModel('selectedAssignment');
const store = useStore();
const countSessionStore = useCountSessionStore();
const { t: $t } = useI18n();
const { wildcardToRegex } = useWildcardToRegex();



const isLoading = computed(() => countSessionStore.loading);
const items = computed(() => countSessionStore.items);
const filteredItems = computed(() => items.value.filter((item) => {
  if (props.searchText) {
    return item.code.includes(props.searchText);
  }
  return true;
}));

const assignedItemKeys = computed(() => {
  const keys = new Set();
  props.assignments?.forEach((assignment) => {
    assignment?.items?.forEach((item) => {
      keys.add(item._key || item.key);
    });
  });
  return keys;
});

function getUser(user_key) {
  return store.getters.operator_list().find((u) => u._key === user_key);
}

function getItemAssignees(item) {
  const itemKey = item._key || item.key;
  const assignees = [];
  props.assignments?.forEach((assignment) => {
    if (assignment.items?.some((i) => (i._key || i.key) === itemKey)) {
      const user = getUser(assignment.user_key);
      if (user) assignees.push(user);
    }
  });
  return assignees;
}

function isItemSelected(item) {
  if (!selectedAssignment.value) return false;
  return selectedAssignment.value.items?.some(
    (i) => (i._key || i.key) === (item._key || item.key),
  );
}

function disableItem(item) {
  if (!props.disableAssignedItems) {
    return false;
  }

  const itemKey = item._key || item.key;
  // Don't disable if item is in current assignment
  if (selectedAssignment.value?.items?.some(i => (i._key || i.key) === itemKey)) {
    return false;
  }
  return assignedItemKeys.value.has(itemKey);
}

function toggleItem(item) {
  if (!selectedAssignment.value) {
    // Note: Parent usually handles default selection, but if list is empty or user specifically deselected
    Notify.create({
      message: $t('warehouse.counting.select_assignment_first'),
      color: 'theme-orange',
    });
    return;
  }

  const assignment = selectedAssignment.value;
  if (!assignment.items) assignment.items = [];

  const itemKey = item._key || item.key;
  const index = assignment.items.findIndex(
    (i) => (i._key || i.key) === itemKey,
  );

  if (index > -1) {
    assignment.items.splice(index, 1);
  } else {
    assignment.items.push({
      _key: item._key,
      code: item.code,
      description: item.description,
    });
  }
}

function selectAll() {
  if (!selectedAssignment.value) {
    Notify.create({
      message: $t('warehouse.counting.select_assignment_first'),
      color: 'theme-orange',
    });
    return;
  }

  const assignment = selectedAssignment.value;
  if (!assignment.items) assignment.items = [];

  filteredItems.value.forEach((item) => {
    if (!disableItem(item) && !isItemSelected(item)) {
      assignment.items.push({
        _key: item._key,
        code: item.code,
        description: item.description,
      });
    }
  });
}

let filterTimeout;

const filterItemsAsync = () => {
  isLoading.value = true;
  clearTimeout(filterTimeout);

  // Small delay to allow UI to update (show spinner)
  filterTimeout = setTimeout(() => {
    let result = props.items;

    // Apply search filter
    if (props.searchText) {
      const regex = wildcardToRegex(props.searchText);
      result = result.filter((p) => regex.test(p.code));
    }

    // Apply multi-assignment filter
    if (props.showMultiAssignedOnly) {
      result = result.filter((item) => {
        const assignees = getItemAssignees(item);
        return assignees.length > 1;
      });
    }

    filteredItems.value = result;

    // Calculate stats for parent
    // Note: centerColumnMultiAssignedCount was calculated based on *filtered* items in original logic
    const multiAssignedCount = result.filter((item) => {
        const assignees = getItemAssignees(item);
        return assignees.length > 1;
    }).length;

    emit('update:stats', {
      shownCount: result.length,
      totalCount: props.items.length,
      multiAssignedCount: multiAssignedCount
    });

    isLoading.value = false;
  }, 50);
};

watch(
  [
    () => props.items,
    () => props.searchText,
    () => props.showMultiAssignedOnly,
    // We might need to re-filter if assignments change (for multi-assigned filter)
    // but that might be too heavy. The original logic was a computed property, so it did.
    () => props.assignments
  ],
  filterItemsAsync,
  { immediate: true }
);

defineExpose({
  selectAll,
});
</script>
