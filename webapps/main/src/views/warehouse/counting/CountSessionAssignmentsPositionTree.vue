<template>
  <div class="col fit column relative-position" style="max-height: 100%; overflow-y: auto">
    <LoadingSignal v-if="isLoading" />

    <q-tree
      v-else
      class="col"
      :nodes="filteredNodes"
      accordion
      node-key="key"
      tick-strategy="strict"
      v-model:expanded="expandedNodes"
      @lazy-load="onLazyLoad"
    >
      <template #default-header="prop">
        <div class="row items-center full-width">
          <q-checkbox
            :model-value="isPositionSelected(prop.node.key)"
            @update:model-value="togglePosition(prop.node)"
            @click.stop
          />
          <span class="q-ml-sm"># {{ prop.node.label }}</span>
          <q-space />
          <template v-if="getItemAssignees({ key: prop.node.key }).length > 0">
            <template v-if="getItemAssignees({ key: prop.node.key }).length === 1">
              <BaseUserAvatar
                :user="getItemAssignees({ key: prop.node.key })[0]"
                :show-name="false"
                size="32px"
                dense
                class="q-ml-sm"
              >
                <q-tooltip>
                  {{ getItemAssignees({ key: prop.node.key })[0].name }} {{ getItemAssignees({ key: prop.node.key })[0].surname }}
                </q-tooltip>
              </BaseUserAvatar>
            </template>
            <template v-else>
              <div class="row items-center q-gutter-x-xs">
                <q-icon
                  name="mdi-account-group"
                  size="20px"
                >
                  <q-tooltip>
                    <div v-for="user in getItemAssignees({ key: prop.node.key })" :key="user._key">
                      {{ user.name }} {{ user.surname }}
                    </div>
                  </q-tooltip>
                </q-icon>
                <span class="text-caption">{{ getItemAssignees({ key: prop.node.key }).length }}</span>
              </div>
            </template>
          </template>
        </div>
      </template>
    </q-tree>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';
import BaseUserAvatar from '@/components/BaseUserAvatar.vue';
import LoadingSignal from '@/components/LoadingSignal.vue';
import { useWildcardToRegex } from '@/composables/useWildcardToRegex';
import { useCountSessionStore } from '@/stores/countSession';

const props = defineProps({
  fullTree: {
    type: Array,
    default: () => [],
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

const selectedAssignment = defineModel('selectedAssignment');

const countSessionStore = useCountSessionStore();
const { t: $t } = useI18n();
const { wildcardToRegex } = useWildcardToRegex();

const isLoading = computed(() => countSessionStore.loading);
const expandedNodes = ref(['IN']);
const tree = computed(() => countSessionStore.positionTree);

onMounted(() => {
  countSessionStore.loadPositions();
});


const assignedItemKeys = computed(() => {
  const keys = new Set();
  props.assignments?.forEach((assignment) => {
    assignment?.items?.forEach((item) => {
      keys.add(item._key || item.key);
    });
  });
  return keys;
});


function isPositionSelected(positionKey) {
  if (!selectedAssignment.value) return false;
  return selectedAssignment.value.items?.some(
    (i) => i.key === positionKey,
  );
}


</script>
