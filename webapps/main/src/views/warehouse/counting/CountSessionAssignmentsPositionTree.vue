<template>
  <div class="col fit column relative-position" style="max-height: 100%; overflow-y: auto">
    <LoadingSignal v-if="isLoading" />

    <q-virtual-scroll
      v-else
      :items="flattenedNodes"
      virtual-scroll-item-size="48"
      v-slot="{ item }"
      class="col"
    >
        <q-item
          :key="item.position_key"
          class="row items-start q-py-xs"
          :style="{ paddingLeft: (item.level * 24 + 16) + 'px' }"
          clickable
          dense
          @click.stop="togglePosition(item)"
        >
          <!-- Expand/collapse button -->
          <q-item-section side>
            <q-btn
              v-if="item.hasChildren"
              flat
              dense
              round
              size="sm"
              padding="4px"
              :icon="expandedKeys.has(item.position_key) ? 'mdi-chevron-down' : 'mdi-chevron-right'"
              @click.stop="toggleExpand(item.position_key)"
            />
            <div v-else style="width: 25px"></div>
          </q-item-section>

          <!-- Checkbox -->
          <q-item-section side>
            <q-checkbox
              :model-value="isPositionSelected(item.position_key)"
              @update:model-value="togglePosition(item)"
              @click.stop
              dense
            />
          </q-item-section>
          <!-- Position label -->

          <q-item-section>
            <div class="q-ml-sm">{{ item.code }}</div>
            <div class="q-ml-sm smaller text-low">{{ item.pathString }}</div>
          </q-item-section>

          <!-- Assignees indicator -->
          <q-item-section side>
            <template v-if="getItemAssignees({ key: item.position_key }).length > 0">
              <template v-if="getItemAssignees({ key: item.position_key }).length === 1">
                <BaseUserAvatar
                  :user="getItemAssignees({ key: item.position_key })[0]"
                  :show_name="false"
                  size="32px"
                  dense
                  class="q-mr-md"
                >
                  <q-tooltip>
                    {{ getItemAssignees({ key: item.position_key })[0].name }} {{ getItemAssignees({ key: item.position_key })[0].surname }}
                  </q-tooltip>
                </BaseUserAvatar>
              </template>
              <template v-else>
                <div class="row items-center q-gutter-x-xs q-mr-sm">
                  <q-icon
                    name="mdi-account-group"
                    size="20px"
                  >
                    <q-tooltip>
                      <div v-for="user in getItemAssignees({ key: item.position_key })" :key="user._key">
                        {{ user.name }} {{ user.surname }}
                      </div>
                    </q-tooltip>
                  </q-icon>
                  <span class="text-caption">{{ getItemAssignees({ key: item.position_key }).length }}</span>
                </div>
              </template>
            </template>
          </q-item-section>
        </q-item>
    </q-virtual-scroll>
  </div>
</template>

<script setup>
import { computed, ref, onMounted, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { useStore } from 'vuex';
import { Notify } from 'quasar';
import BaseUserAvatar from '@/components/BaseUserAvatar.vue';
import LoadingSignal from '@/components/LoadingSignal.vue';
import { useWildcardToRegex } from '@/composables/useWildcardToRegex';
import { useCountSessionStore } from '@/stores/countSession';

const props = defineProps({
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

const countSessionStore = useCountSessionStore();
const store = useStore();
const { t: $t } = useI18n();
const { wildcardToRegex } = useWildcardToRegex();

const isLoading = computed(() => countSessionStore.loading);
const expandedKeys = ref(new Set(['IN']));
const tree = computed(() => countSessionStore.positionTree);
const positionLookup = computed(() => countSessionStore.positionLookup);

onMounted(() => {
  countSessionStore.loadPositions();
});

/**
 * Check if a node matches the current filters
 */
function nodeMatchesFilters(node, posData) {
  // Apply search filter
  if (props.searchText) {
    const searchLower = props.searchText.toLowerCase();
    if (!posData.pathString.toLowerCase().includes(searchLower)) {
      return false;
    }
  }

  // Apply multi-assigned filter
  if (props.showMultiAssignedOnly) {
    const assignees = getItemAssignees({ key: node.position_key });
    if (assignees.length <= 1) {
      return false;
    }
  }

  return true;
}

/**
 * Check if any descendant of a node matches the filters (recursive)
 */
function hasMatchingDescendant(node) {
  if (!node.children || node.children.length === 0) {
    return false;
  }

  for (const child of node.children) {
    const childData = positionLookup.value.get(child.position_key);
    if (!childData) continue;

    if (nodeMatchesFilters(child, childData)) {
      return true;
    }

    // Check descendants recursively
    if (hasMatchingDescendant(child)) {
      return true;
    }
  }

  return false;
}

/**
 * Flatten the tree based on expanded nodes and apply filters
 */
const flattenedNodes = computed(() => {
  const result = [];

  function traverse(nodes, showPath = false) {
    nodes.forEach(node => {
      const posData = positionLookup.value.get(node.position_key);
      if (!posData) return;

      // Check if this node matches filters
      const matches = nodeMatchesFilters(node, posData);
      const hasDescendantMatch = hasMatchingDescendant(node);

      // Include node if:
      // 1. It matches the filters, OR
      // 2. We're showing path to a matching descendant (showPath is true)
      const shouldInclude = matches || (showPath && hasDescendantMatch);

      if (shouldInclude) {
        result.push({
          ...posData,
          hasChildren: node.children && node.children.length > 0
        });
      }

      // Determine if we should expand this node:
      // 1. User manually expanded it, OR
      // 2. It has matching descendants and filtering is active (auto-expand)
      const isManuallyExpanded = expandedKeys.value.has(node.position_key);
      const shouldAutoExpand = (props.searchText || props.showMultiAssignedOnly) && hasDescendantMatch;
      const shouldExpand = isManuallyExpanded || shouldAutoExpand;

      // Recursively process children if expanded
      if (shouldExpand && node.children) {
        // Pass showPath=true if this node matches or we're already showing path
        traverse(node.children, matches || showPath);
      }
    });
  }

  if (tree.value && tree.value.length > 0) {
    traverse(tree.value, false);
  }

  return result;
});

const multiAssignedCount = computed(() => {
  if (!positionLookup.value) return 0;
  let count = 0;
  for (const posData of positionLookup.value.values()) {
    const assignees = getItemAssignees({ key: posData.position_key });
    if (assignees.length > 1) {
      count++;
    }
  }
  return count;
});

// Update stats when flattenedNodes changes
watch([flattenedNodes, multiAssignedCount, () => positionLookup.value.size], ([newNodes, newMultiCount, newTotalCount]) => {
  emit('update:stats', {
    shownCount: newNodes.length,
    totalCount: newTotalCount,
    multiAssignedCount: newMultiCount
  });
}, { immediate: true });

const assignedItemKeys = computed(() => {
  const keys = new Set();
  props.assignments?.forEach((assignment) => {
    assignment?.items?.forEach((item) => {
      keys.add(item._key || item.key);
    });
  });
  return keys;
});

/**
 * Toggle expand/collapse state for a node
 */
function toggleExpand(positionKey) {
  if (expandedKeys.value.has(positionKey)) {
    expandedKeys.value.delete(positionKey);
  } else {
    expandedKeys.value.add(positionKey);
  }
  // Trigger reactivity
  expandedKeys.value = new Set(expandedKeys.value);
}

/**
 * Check if a position is selected (directly or via ancestor)
 */
function isPositionSelected(positionKey) {
  if (!selectedAssignment.value) return false;

  const items = selectedAssignment.value.items || [];
  const posData = positionLookup.value.get(positionKey);
  if (!posData) return false;

  // Check direct assignment
  if (items.find(i => i.key === positionKey)) return true;

  // Check if any ancestor is assigned
  for (const ancestorKey of posData.ancestors) {
    if (items.find(i => i.key === ancestorKey)) {
      return true;
    }
  }

  return false;
}

/**
 * Smart toggle with sibling materialization
 * Implements "lowest complete level" assignment strategy
 */
function togglePosition(item) {
  if (!selectedAssignment.value) {
    Notify.create({
      message: $t('warehouse.counting.select_assignment_first'),
      color: 'theme-orange',
    });
    return;
  }

  const positionKey = item.position_key;
  const posData = positionLookup.value.get(positionKey);
  if (!posData) return;

  const items = selectedAssignment.value.items;
  const assignedKeys = new Set(items.map(i => i.key));

  if (isPositionSelected(positionKey)) {
    // UNSELECT

    const ownAssignment = items.find(i => i.key === positionKey);

    if (ownAssignment) {
      // Case 1: Directly assigned → Just remove it
      const index = items.indexOf(ownAssignment);
      items.splice(index, 1);
    } else {
      // Case 2: Assigned via ancestor → Materialize siblings, exclude this branch

      // Find the assigned ancestor
      const assignedAncestor = posData.ancestors.find(aKey => assignedKeys.has(aKey));

      if (assignedAncestor) {
        // Remove the ancestor from assignments
        const ancestorIndex = items.findIndex(i => i.key === assignedAncestor);
        if (ancestorIndex > -1) {
          items.splice(ancestorIndex, 1);
        }

        // Add all direct children of ancestor, except this branch
        const ancestorNode = countSessionStore.findNodeInTree(assignedAncestor);

        if (ancestorNode?.children) {
          ancestorNode.children.forEach(child => {
            const childData = positionLookup.value.get(child.position_key);

            // Skip this position and any sibling that contains this position
            if (child.position_key === positionKey) return;
            if (childData && childData.descendants.includes(positionKey)) return;

            // Add sibling
            items.push({
              key: child.position_key,
              code: child.code,
              label: child.code
            });
          });
        }
      }
    }

    // Remove all descendants (they're implicitly removed)
    const descendantKeys = new Set(posData.descendants);
    selectedAssignment.value.items = items.filter(i => !descendantKeys.has(i.key));

  } else {
    // SELECT

    // Remove any descendants (parent takes precedence)
    const descendantKeys = new Set(posData.descendants);
    let filteredItems = items.filter(i => !descendantKeys.has(i.key));
    selectedAssignment.value.items = filteredItems;

    // Check if all siblings are now selected → consolidate to parent
    if (posData.parent_key) {
      const parentNode = countSessionStore.findNodeInTree(posData.parent_key);

      if (parentNode?.children) {
        const siblingKeys = parentNode.children.map(c => c.position_key);
        const selectedSiblings = siblingKeys.filter(sk =>
          filteredItems.find(i => i.key === sk) || sk === positionKey
        );

        // If all siblings would be selected, replace with parent
        if (selectedSiblings.length === siblingKeys.length) {
          filteredItems = filteredItems.filter(i => !siblingKeys.includes(i.key));
          filteredItems.push({
            key: posData.parent_key,
            code: positionLookup.value.get(posData.parent_key).code,
            label: positionLookup.value.get(posData.parent_key).code
          });
          selectedAssignment.value.items = filteredItems;
          return;
        }
      }
    }

    // Add this position
    filteredItems.push({
      key: positionKey,
      code: posData.code,
      label: posData.code
    });
    selectedAssignment.value.items = filteredItems;
  }
}

/**
 * Get users assigned to a specific position
 */
function getItemAssignees(item) {
  const itemKey = item._key || item.key;
  const assignees = [];

  props.assignments?.forEach((assignment) => {
    // Check if this position or any ancestor is in the assignment
    const posData = positionLookup.value.get(itemKey);
    if (!posData) return;

    const isAssigned = assignment.items?.some((i) => {
      const assignedKey = i._key || i.key;
      // Check if this position or any ancestor is assigned
      return assignedKey === itemKey || posData.ancestors.includes(assignedKey);
    });

    if (isAssigned) {
      const user = store.getters.operator_list().find((u) => u._key === assignment.user_key);
      if (user) assignees.push(user);
    }
  });

  return assignees;
}

/**
 * Select all visible positions (for "Select All" button)
 */
function selectAll() {
  if (!selectedAssignment.value) {
    Notify.create({
      message: $t('warehouse.counting.select_assignment_first'),
      color: 'theme-orange',
    });
    return;
  }

  flattenedNodes.value.forEach(node => {
    if (!isPositionSelected(node.position_key)) {
      togglePosition(node);
    }
  });
}

// Expose selectAll for parent component
defineExpose({ selectAll });

</script>
