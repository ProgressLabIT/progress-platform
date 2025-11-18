<template>
  <q-tab-panel :name="2" class="q-px-none">
    <div class="row full-height">

      <!-- LEFT COLUMN: ASSIGNMENT LIST -->
      <div class="col-3 column">
        <!-- ASSIGNMENT LIST -->
        <div class="row items-center justify-between q-my-xs q-px-md">
          <div class="text-h5 uppercase">
            {{ $t('warehouse.counting.assignments') }}
          </div>
          <div class="col-auto row items-center q-gutter-x-sm">
            <div class="smaller text-low">
              {{ coveragePercentage.toFixed(1) }}%
            </div>
            <q-circular-progress
              size="18px"
              :value="coveragePercentage"
              track-color="theme-grey"
              color="white"
            />
          </div>
        </div>

        <q-separator inset class="q-my-sm" />

        <!-- ADD ASSIGNMENT BUTTON -->
        <BaseAutocompleteUser
            dense
            :label="$capitalize($t('warehouse.counting.add_assignment'))"
            :clearable="false"
            :key-only="true"
            @select="addAssignment"
            class="q-mx-md q-my-sm"
          />

        <q-scroll-area class="col" style="max-height: 100%">
          <q-list>
            <q-item
              v-for="item in assignments"
              :key="item.user_key"
              class="assignment-item"
              :class="selectedAssignment?.user_key === item.user_key ? 'selected-assignment text-high' : ''"
              clickable
              @click="selectedAssignment = item"
            >
              <q-item-section>
                <BaseUserAvatar
                  :user="getUser(item.user_key)"
                  :show-name="true"
                  dense
                />
              </q-item-section>
              <q-item-section side>
                {{ getAssignmentCount(item) }}
              </q-item-section>
              <q-item-section side>
                <q-btn
                  flat
                  round
                  icon="mdi-delete"
                  size="sm"
                  @click.stop="removeAssignment(item.user_key)"
                />
              </q-item-section>
            </q-item>
          </q-list>
        </q-scroll-area>
      </div>

      <q-separator vertical />

      <!-- CENTER COLUMN: AVAILABLE ITEMS -->
      <div class="col column full-height">
        <div class="row items-center justify-between q-col-gutter-x-lg q-px-md">
          <div class="col-auto row items-center q-gutter-x-sm">
            <span class="q-mr-sm text-h5 uppercase">
              {{ $t('shown', 2) }}
            </span>
            <q-chip color="theme-grey" size="sm">
              <strong>
                {{ filteredItems?.length }}
              </strong>
              <span class="q-mx-xs">
                {{ $t('of') }}
              </span>
              <strong>
                {{ totalItemCount }}
              </strong>
            </q-chip>
            <q-icon
              name="mdi-account-group"
              size="20px"
              class="q-ml-sm"
            />
            <q-chip
              color="theme-grey"
              size="sm"
              clickable
              @click="showMultiAssignedOnlyCenter = !showMultiAssignedOnlyCenter"
              :outline="!showMultiAssignedOnlyCenter"
            >
              <strong>{{ centerColumnMultiAssignedCount }}</strong>
            </q-chip>
          </div>
          <q-btn
            size="xs"
            padding="xs sm"
            icon="mdi-checkbox-marked-outline"
            :label="$t('select_all')"
            color="theme-grey"
            class="q-ml-md"
            @click="selectAllItems"
          />
        </div>

        <q-separator inset class="q-my-sm" />

        <div class="col-auto row q-my-sm items-center q-px-md justify-between q-gutter-x-lg">
          <q-input
            v-model="searchText"
            filled
            dense
            debounce="200"
            :placeholder="$capitalize($t('search'))"
            class="col"
          >
            <template #append>
              <q-icon name="mdi-magnify" />
            </template>
          </q-input>
        </div>

        <q-virtual-scroll
          v-if="sessionType === 'product'"
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
                >
                  <q-tooltip>
                    {{ getItemAssignees(item)[0].name }} {{ getItemAssignees(item)[0].surname }}
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

        <div
          v-else
          class="col fit column"
          style="max-height: 100%; overflow-y: auto"
        >
          <q-input
            v-model="searchText"
            filled
            dense
            debounce="200"
            :placeholder="$t('search')"
            class="q-mb-sm col-auto"
          >
            <template #prepend>
              <q-icon name="mdi-magnify" />
            </template>
          </q-input>
          <q-tree
            v-if="positionTreeNodes.length > 0"
            class="col"
            v-model:ticked="selectedPositions"
            tick-strategy="leaf"
            :nodes="filteredPositionTreeNodes"
            accordion
            node-key="key"
            :tick-strategy="'leaf'"
            @update:selected="onPositionSelection"
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
      </div>

      <q-separator vertical />

      <!-- RIGHT COLUMN: SELECTED ITEMS -->
      <div class="col column full-height">
        <div class="col-auto row items-center q-px-md justify-between">
          <div class="row items-center q-gutter-x-sm">
            <span class="text-h5 uppercase">
              {{ $t('warehouse.counting.selected') }}
            </span>
            <q-chip color="theme-grey" size="sm">
              <strong>
                {{ filteredAssignedItems?.length }}
              </strong>
              <span class="q-mx-xs">
                {{ $t('of') }}
              </span>
              <strong>
                {{ selectedItemsForAssignment?.length }}
              </strong>
            </q-chip>
            <q-icon
              name="mdi-account-group"
              size="20px"
              class="q-ml-sm"
            />
            <q-chip
              color="theme-grey"
              size="sm"
              clickable
              @click="showMultiAssignedOnlyRight = !showMultiAssignedOnlyRight"
              :outline="!showMultiAssignedOnlyRight"
            >
              <strong>{{ rightColumnMultiAssignedCount }}</strong>
            </q-chip>
          </div>
          <q-btn
            size="xs"
            padding="xs sm"
            icon="mdi-checkbox-blank-off-outline"
            :label="$t('deselect_all')"
            color="theme-grey"
            class="q-ml-md"
            @click="clearSelectedItems"
          >
          </q-btn>
        </div>

        <q-separator inset class="q-my-sm" />

        <div class="q-px-md col-auto q-my-sm">
          <q-input
            v-model="selectedItemsSearchText"
            filled
            dense
            debounce="200"
            :placeholder="$capitalize($t('search'))"
          >
            <template #append>
              <q-icon name="mdi-magnify" />
            </template>
          </q-input>
        </div>
        <q-virtual-scroll
          v-slot="{ item }"
          class="col fit"
          style="max-height: 100%"
          :items="filteredAssignedItems"
        >
          <q-item :key="item._key || item.key" style="min-height: none">
            <q-item-section side>
              <q-btn
                flat
                round
                icon="mdi-close"
                size="sm"
                @click="removeSelectedItem(item)"
              />
            </q-item-section>
            <q-item-section>
              <q-item-label class="highlight">
                {{ item.code || item.label }}
              </q-item-label>
              <q-item-label
                v-if="item.description"
                caption
                class="ellipsis"
              >
                {{ item.description }}
              </q-item-label>
            </q-item-section>
            <q-item-section v-if="getItemAssignees(item).length > 1" side>
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
            </q-item-section>
          </q-item>
        </q-virtual-scroll>
      </div>
    </div>
  </q-tab-panel>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { useStore } from 'vuex';
import { Notify } from 'quasar';
import { useWildcardToRegex } from '@/composables/useWildcardToRegex';
import BaseAutocompleteUser from '@/components/BaseAutocompleteUser.vue';
import BaseUserAvatar from '@/components/BaseUserAvatar.vue';

const props = defineProps({
  sessionType: {
    type: String,
    required: true,
  },
  items: {
    type: Array,
    required: true,
  },
  positionTreeNodes: {
    type: Array,
    default: () => [],
  },
  disableAssignedItems: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(['update:disableAssignedItems']);

const { t: $t } = useI18n();
const store = useStore();
const { wildcardToRegex } = useWildcardToRegex();

const searchText = ref('');
const selectedAssignment = ref(null);
const selectedPositions = ref([]);
const selectedItemsSearchText = ref('');
const showMultiAssignedOnlyCenter = ref(false);
const showMultiAssignedOnlyRight = ref(false);

const assignments = ref([]); // [{ user_key, items: [] }]

// Computed properties
const filteredItems = computed(() => {
  let result = props.items;

  if (props.sessionType === 'product') {
    // Apply search filter
    if (searchText.value) {
      const regex = wildcardToRegex(searchText.value);
      result = result.filter((p) => regex.test(p.code));
    }

    // Apply multi-assignment filter for center column
    if (showMultiAssignedOnlyCenter.value) {
      result = result.filter((item) => {
        const assignees = getItemAssignees(item);
        return assignees.length > 1;
      });
    }
  }

  return result;
});

const filteredAssignedItems = computed(() => {
  let result = selectedItemsForAssignment.value;

  // Apply search filter
  if (selectedItemsSearchText.value) {
    const regex = wildcardToRegex(selectedItemsSearchText.value);
    result = result.filter((a) => regex.test(a.code || a.label));
  }

  // Apply multi-assignment filter for right column
  if (showMultiAssignedOnlyRight.value) {
    result = result.filter((item) => {
      const assignees = getItemAssignees(item);
      return assignees.length > 1;
    });
  }

  return result;
});

const totalItemCount = computed(() => {
  if (props.sessionType === 'product') {
    return props.items.length;
  } else {
    // For positions, count all nodes in the tree
    const countNodes = (nodes) => {
      return nodes.reduce((count, node) => {
        return count + 1 + (node.children ? countNodes(node.children) : 0);
      }, 0);
    };
    return props.positionTreeNodes.length > 0
      ? countNodes(props.positionTreeNodes)
      : props.items.length; // Fallback to flat list
  }
});

const filteredPositionTreeNodes = computed(() => {
  const regex = searchText.value ? wildcardToRegex(searchText.value) : null;

  const filterTree = (nodes) => {
    return nodes
      .map((node) => {
        const matchesSearch = !regex || regex.test(node.label);
        const matchesMultiAssignment = !showMultiAssignedOnlyCenter.value || (() => {
          const assignees = getItemAssignees({ key: node.key });
          return assignees.length > 1;
        })();

        const filteredChildren = node.children
          ? filterTree(node.children)
          : undefined;

        if ((matchesSearch && matchesMultiAssignment) || (filteredChildren && filteredChildren.length > 0)) {
          return {
            ...node,
            children: filteredChildren,
          };
        }
        return null;
      })
      .filter((n) => n !== null);
  };

  return filterTree(props.positionTreeNodes);
});

const assignedItemKeys = computed(() => {
  const keys = new Set();
  assignments.value.forEach((assignment) => {
    assignment.items?.forEach((item) => {
      keys.add(item._key || item.key);
    });
  });
  return keys;
});

const selectedItemsForAssignment = computed(() => {
  if (!selectedAssignment.value) return [];
  return selectedAssignment.value.items || [];
});

const coveragePercentage = computed(() => {
  if (totalItemCount.value === 0) {
     return 0
  };
  return (assignedItemKeys.value.size / totalItemCount.value) * 100;
});

const centerColumnMultiAssignedCount = computed(() => {
  return filteredItems.value.filter((item) => {
    const assignees = getItemAssignees(item);
    return assignees.length > 1;
  }).length;
});

const rightColumnMultiAssignedCount = computed(() => {
  return selectedItemsForAssignment.value.filter((item) => {
    const assignees = getItemAssignees(item);
    return assignees.length > 1;
  }).length;
});

// Methods
function getUser(user_key) {
  return store.getters.operator_list().find((u) => u._key === user_key);
}

function getAssignmentCount(assignment) {
  return assignment.items?.length || 0;
}

function addAssignment(user_key) {
  if (!user_key || assignments.value.some((a) => a.user_key === user_key)) {
    return;
  }
  assignments.value.push({
    user_key,
    items: [],
  });
  selectedAssignment.value = assignments.value[assignments.value.length - 1];
}

function removeAssignment(user_key) {
  const index = assignments.value.findIndex((a) => a.user_key === user_key);
  if (index > -1) {
    assignments.value.splice(index, 1);
    if (
      selectedAssignment.value?.user_key === user_key ||
      assignments.value.length === 0
    ) {
      selectedAssignment.value = null;
    } else {
      selectedAssignment.value = assignments.value[0];
    }
  }
}

function isItemSelected(item) {
  if (!selectedAssignment.value) return false;
  return selectedAssignment.value.items?.some(
    (i) => (i._key || i.key) === (item._key || item.key),
  );
}

function disableItem(item) {
  // If toggle is off, allow all items to be selected
  if (!props.disableAssignedItems) {
    return false;
  }

  const itemKey = item._key || item.key;
  // Don't disable if item is in current assignment
  if (selectedAssignment.value?.items?.some(i => (i._key || i.key) === itemKey)) {
    return false;
  }
  // Disable if assigned to another user (only when toggle is on)
  return assignedItemKeys.value.has(itemKey);
}

function getItemAssignees(item) {
  const itemKey = item._key || item.key;
  const assignees = [];
  assignments.value.forEach((assignment) => {
    if (assignment.items?.some((i) => (i._key || i.key) === itemKey)) {
      const user = getUser(assignment.user_key);
      if (user) assignees.push(user);
    }
  });
  return assignees;
}

function toggleItem(item) {
  if (!selectedAssignment.value) {
    // Auto-select first assignment or create one
    if (assignments.value.length === 0) {
      Notify.create({
        message: $t('warehouse.counting.select_assignment_first'),
        color: 'theme-orange',
      });
      return;
    }
    selectedAssignment.value = assignments.value[0];
  }

  const assignment = selectedAssignment.value;
  if (!assignment.items) assignment.items = [];

  const index = assignment.items.findIndex(
    (i) => (i._key || i.key) === (item._key || item.key),
  );

  if (index > -1) {
    assignment.items.splice(index, 1);
  } else {
    assignment.items.push(item);
  }
}

function isPositionSelected(positionKey) {
  if (!selectedAssignment.value) return false;
  return selectedAssignment.value.items?.some(
    (i) => i.key === positionKey,
  );
}

function togglePosition(node) {
  if (!selectedAssignment.value) {
    if (assignments.value.length === 0) {
      Notify.create({
        type: 'warning',
        message: $t('warehouse.counting.session.select_assignment_first'),
        color: 'theme-orange',
      });
      return;
    }
    selectedAssignment.value = assignments.value[0];
  }

  const assignment = selectedAssignment.value;
  if (!assignment.items) assignment.items = [];

  // Get all children positions recursively
  const getAllChildren = (n) => {
    const children = [n.key];
    if (n.children) {
      n.children.forEach((child) => {
        children.push(...getAllChildren(child));
      });
    }
    return children;
  };

  const positionKeys = getAllChildren(node);
  const isSelected = positionKeys.some((key) =>
    assignment.items.some((i) => i.key === key),
  );

  if (isSelected) {
    // Remove this position and all children
    assignment.items = assignment.items.filter(
      (i) => !positionKeys.includes(i.key),
    );
  } else {
    // Add this position and all children using tree node data
    const addPositionsFromNode = (n) => {
      if (!assignment.items.some((i) => i.key === n.key)) {
        assignment.items.push({
          key: n.key,
          code: n.label,
          label: n.label,
        });
      }
      if (n.children) {
        n.children.forEach(addPositionsFromNode);
      }
    };
    addPositionsFromNode(node);
  }
}

function onPositionSelection(selected) {
  // Handle position tree selection
  // This is handled by togglePosition
}

function removeSelectedItem(item) {
  if (!selectedAssignment.value) return;
  const assignment = selectedAssignment.value;
  if (!assignment.items) return;

  const index = assignment.items.findIndex(
    (i) => (i._key || i.key) === (item._key || item.key),
  );
  if (index > -1) {
    assignment.items.splice(index, 1);
  }
}

function clearSelectedItems() {
  if (!selectedAssignment.value) return;

  const assignment = selectedAssignment.value;
  if (!assignment.items) return;

  // Get keys of items that are currently filtered/visible
  const visibleKeys = new Set(
    filteredAssignedItems.value.map((item) => item._key || item.key)
  );

  // Remove only visible items
  assignment.items = assignment.items.filter(
    (item) => !visibleKeys.has(item._key || item.key)
  );
}

function selectAllItems() {
  if (!selectedAssignment.value) {
    if (assignments.value.length === 0) {
      Notify.create({
        message: $t('warehouse.counting.select_assignment_first'),
        color: 'theme-orange',
      });
      return;
    }
    selectedAssignment.value = assignments.value[0];
  }

  const assignment = selectedAssignment.value;
  if (!assignment.items) assignment.items = [];

  if (props.sessionType === 'product') {
    // Add visible, non-disabled products
    filteredItems.value.forEach((item) => {
      if (!disableItem(item) && !isItemSelected(item)) {
        assignment.items.push(item);
      }
    });
  } else {
    // For positions, traverse the filtered tree and add visible, non-disabled positions
    const addPositionsFromTree = (nodes) => {
      nodes.forEach((node) => {
        if (!disableItem({ key: node.key }) && !isPositionSelected(node.key)) {
          assignment.items.push({
            key: node.key,
            code: node.label,
            label: node.label,
          });
        }
        if (node.children) {
          addPositionsFromTree(node.children);
        }
      });
    };
    addPositionsFromTree(filteredPositionTreeNodes.value);
  }
}

// Expose methods and data that parent needs
defineExpose({
  assignments,
  selectedAssignment,
});
</script>

<style scoped lang="sass">

.selected-assignment::before
  content: ''
  position: absolute
  left: 0
  top: 0
  bottom: 0
  width: 2px
  background-color: var(--q-primary)

.selected-assignment :deep(.q-item__section)
  font-weight: 600
</style>

