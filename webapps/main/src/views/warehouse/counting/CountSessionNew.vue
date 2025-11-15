<template>
  <BaseDialog :show="true" :get-dialog-ref="getDialogRef" @close="onDialogHide">
    <q-card class="surface1 column" style="height: 90vh; min-width: 90vw">
      <q-card-section class="row items-center justify-between col-auto q-pb-none">
        <div class="display text-h3">
          {{ $t('warehouse.counting.session_new') }}
        </div>
        <q-tabs
          v-model="step"
          dense
          active-color="primary"
          indicator-color="primary"
          class="col-auto"
          align="right"
        >
          <q-tab
            :name="1"
            :label="$t('warehouse.counting.session_data')"
            icon="mdi-information"
          />
          <q-tab
            :name="2"
            :label="$t('warehouse.counting.assignments')"
            icon="mdi-account-multiple"
          />
        </q-tabs>
      </q-card-section>

      <q-separator />

      <q-tab-panels
        v-model="step"
        class="col surface1"
      >
        <!-- TAB 1: SESSION DATA -->
        <q-tab-panel :name="1">
          <div class="column q-gutter-y-lg q-pa-md">

            <div class="row items-center q-gutter-x-xl">
              <div class="text-body2 text-low col-auto">
                {{ $t('warehouse.counting.type') }}
              </div>

              <div class="col-auto">
                <q-btn-toggle
                  v-model="sessionData.type"
                  :options="sessionTypeOptions"
                  size="12px"
                  padding="xs md"
                />
              </div>
            </div>


            <div class="col-auto">
              <q-input
                v-model="sessionData.code"
                filled
                :label="$capitalize($t('code'))"
                :hint="$t('warehouse.counting.code_hint')"
              />
            </div>

            <q-input
              v-model="sessionData.description"
              filled
              autogrow
              :label="$t('description')"
            />

            <div class="row q-gutter-md">
              <q-input
                v-model="sessionData.scheduled_start"
                filled
                :label="$t('warehouse.counting.scheduled_start')"
                :placeholder="$t('date_format')"
                input-class="cursor-pointer"
                class="col"
                label-slot
                stack-label
              >
                <template #append>
                  <q-icon name="mdi-calendar" />
                </template>
                <q-popup-proxy anchor="center middle" self="center middle" @hide="blur">
                  <q-date v-model="sessionData.scheduled_start" minimal>
                    <div class="row items-center justify-end">
                      <q-btn v-close-popup :label="$t('close')" color="primary" flat />
                    </div>
                  </q-date>
                </q-popup-proxy>
                <template #label>
                  {{ $t('warehouse.counting.scheduled_start') }}
                </template>
              </q-input>
              <q-input
                v-model="sessionData.scheduled_end"
                filled
                :label="$t('warehouse.counting.scheduled_end')"
                :placeholder="$t('date_format')"
                input-class="cursor-pointer"
                class="col"
                label-slot
                stack-label
              >
                <template #append>
                  <q-icon name="mdi-calendar" />
                </template>
                <q-popup-proxy anchor="center middle" self="center middle" @hide="blur">
                  <q-date v-model="sessionData.scheduled_end" minimal>
                    <div class="row items-center justify-end">
                      <q-btn v-close-popup :label="$t('close')" color="primary" flat />
                    </div>
                  </q-date>
                </q-popup-proxy>
                <template #label>
                  {{ $t('warehouse.counting.scheduled_end') }}
                </template>
              </q-input>
            </div>

            <q-checkbox
              v-model="sessionData.blind_mode"
              :label="$t('warehouse.counting.blind_mode')"
            />
          </div>
        </q-tab-panel>

        <!-- TAB 2: ASSIGNMENTS -->
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
               <!-- ADD ASSIGNMENT BUTTON -->

              <q-separator inset />

               <BaseAutocompleteUser
                  dense
                  :label="$capitalize($t('warehouse.counting.add_assignment'))"
                  :clearable="false"
                  :key-only="true"
                  @select="addAssignment"
                  class="q-mx-md q-mt-md"
                />
            </div>

            <q-separator vertical />

            <!-- CENTER COLUMN: AVAILABLE ITEMS -->
            <div class="col column full-height">
              <div class="row items-center justify-between q-col-gutter-x-lg q-px-md">
                <div class="col-auto">
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
                v-if="sessionData.type === 'product'"
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
                      :model-value="assignedItemKeys.has(item._key || item.key)"
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
                  <q-item-section v-if="disableItem(item)" side>
                    <BaseUserAvatar
                      :user="getAssignedUser(item)"
                      :show_name="false"
                      size="32px"
                      dense
                    />
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
                      <BaseUserAvatar
                        v-if="disableItem({ key: prop.node.key })"
                        :user="getAssignedUser({ key: prop.node.key })"
                        :show-name="false"
                        size="32px"
                        dense
                        class="q-ml-sm"
                      />
                    </div>
                  </template>
                </q-tree>
              </div>
            </div>

            <q-separator vertical />

            <!-- RIGHT COLUMN: SELECTED ITEMS -->
            <div class="col column full-height">
              <div class="col-auto row items-center q-px-md justify-between">
                <div class="text-h5 uppercase">
                  {{ $t('warehouse.counting.selected') }}
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
                </q-item>
              </q-virtual-scroll>
            </div>
          </div>
        </q-tab-panel>
      </q-tab-panels>

      <q-separator />

      <q-card-section class="col-auto">
        <div class="row items-center q-gutter-x-sm justify-end">
          <q-btn
            :label="$t('cancel')"
            color="theme-grey"
            @click="onDialogCancel"
          />
          <q-btn
            v-if="step > 1"
            :label="$t('back')"
            color="theme-grey"
            @click="step--"
          />
          <q-btn
            v-if="step < 2"
            :label="$t('next')"
            color="primary"
            @click="step++"
          />
          <q-btn
            v-else
            :label="$t('create')"
            color="primary"
            :loading="saving"
            @click="createSession"
          />
        </div>
      </q-card-section>
    </q-card>
  </BaseDialog>
</template>

<script setup>
import { useDialogPluginComponent } from 'quasar';
import { ref, computed, watch, onMounted, reactive } from 'vue';
import { useI18n } from 'vue-i18n';
import { useStore } from 'vuex';
import { api } from '@/boot/axios';
import { Notify } from 'quasar';
import { useWildcardToRegex } from '@/composables/useWildcardToRegex';
import BaseDialog from '@/components/BaseDialog.vue';
import BaseAutocompleteUser from '@/components/BaseAutocompleteUser.vue';
import BaseUserAvatar from '@/components/BaseUserAvatar.vue';

const props = defineProps({});

defineEmits(useDialogPluginComponent.emitsObject);

const { dialogRef, onDialogHide, onDialogOK, onDialogCancel } = useDialogPluginComponent();
const getDialogRef = () => dialogRef;

const { t: $t } = useI18n();
const store = useStore();
const { wildcardToRegex } = useWildcardToRegex();

const step = ref(1);
const saving = ref(false);
const searchText = ref('');
const selectedAssignment = ref(null);
const selectedPositions = ref([]);
const selectedItemsSearchText = ref('');

const sessionData = reactive({
  code: '',
  description: '',
  type: 'product', // 'product' or 'position'
  blind_mode: true,
  scheduled_start: null,
  scheduled_end: null,
});

const assignments = ref([]); // [{ user_key, items: [] }]
const items = ref([]); // Unified list: products or positions depending on type
const positionTreeNodes = ref([]);

const sessionTypeOptions = computed(() => [
  { label: $t('warehouse.counting.by_product'), value: 'product' },
  { label: $t('warehouse.counting.by_position'), value: 'position' },
]);

// Computed properties
const filteredItems = computed(() => {
  if (sessionData.type !== 'product') return items.value;
  if (!searchText.value) return items.value;

  const regex = wildcardToRegex(searchText.value);
  console.log(regex)
  return items.value.filter((p) => regex.test(p.code));
});

const filteredAssignedItems = computed(() => {
  if (!selectedItemsSearchText.value) {return selectedItemsForAssignment.value};
  const regex = wildcardToRegex(selectedItemsSearchText.value);
  return selectedItemsForAssignment.value.filter((a) => regex.test(a.code));
});

const totalItemCount = computed(() => {
  if (sessionData.type === 'product') {
    return items.value.length;
  } else {
    // For positions, count all nodes in the tree
    const countNodes = (nodes) => {
      return nodes.reduce((count, node) => {
        return count + 1 + (node.children ? countNodes(node.children) : 0);
      }, 0);
    };
    return positionTreeNodes.value.length > 0
      ? countNodes(positionTreeNodes.value)
      : items.value.length; // Fallback to flat list
  }
});

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

  if (sessionData.type === 'product') {
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


const filteredPositionTreeNodes = computed(() => {
  if (!searchText.value) {
    return positionTreeNodes.value;
  }
  const regex = wildcardToRegex(searchText.value);
  const filterTree = (nodes) => {
    return nodes
      .map((node) => {
        const matches = regex.test(node.label);
        const filteredChildren = node.children
          ? filterTree(node.children)
          : undefined;
        if (matches || (filteredChildren && filteredChildren.length > 0)) {
          return {
            ...node,
            children: filteredChildren,
          };
        }
        return null;
      })
      .filter((n) => n !== null);
  };
  return filterTree(positionTreeNodes.value);
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
  const itemKey = item._key || item.key;
  // Don't disable if item is in current assignment
  if (selectedAssignment.value?.items?.some(i => (i._key || i.key) === itemKey)) {
    return false;
  }
  // Disable if assigned to another user
  return assignedItemKeys.value.has(itemKey);
}

function getAssignedUser(item) {
  const itemKey = item._key || item.key;
  // Find which assignment contains this item
  const assignment = assignments.value.find((assignment) =>
    assignment.items?.some((i) => (i._key || i.key) === itemKey),
  );
  return assignment ? getUser(assignment.user_key) : null;
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

async function loadItems() {
  if (sessionData.type === 'product') {
    await loadProducts();
  } else {
    await loadPositions();
  }
}

async function loadProducts() {
  try {
    const { data } = await api.get('/product', {
      params: { active_only: true, limit: null },
    });
    items.value = data;
  } catch (error) {
    console.error('Error loading products:', error);
    items.value = [];
  }
}

async function loadPositions() {
  try {
    // Build tree structure using position hierarchy
    try {
      const { data: hierarchyData } = await api.get('/position-hierarchy', {
        params: { position_key: 'IN' },
      });

      if (hierarchyData && hierarchyData.length > 0) {
        const convertNode = (node) => {
          const children = node.children
            ? node.children.map(convertNode).filter((c) => c)
            : undefined;
          return {
            key: node.position_key,
            label: node.code || node.position_key,
            children: children && children.length > 0 ? children : undefined,
          };
        };

        positionTreeNodes.value = hierarchyData.map(convertNode);
      } else {
        // Fallback: fetch flat list if hierarchy is empty
        const { data } = await api.get('/position', {
          params: { limit: null },
        });
        items.value = data;
        positionTreeNodes.value = data
          .filter((p) => !p.deleted)
          .map((p) => ({
            key: p._key,
            label: p.code || p._key,
          }));
      }
    } catch (hierarchyError) {
      console.warn('Could not load position hierarchy, using flat list:', hierarchyError);
      // Fallback: fetch flat list
      const { data } = await api.get('/position', {
        params: { limit: null },
      });
      items.value = data;
      positionTreeNodes.value = data
        .filter((p) => !p.deleted)
        .map((p) => ({
          key: p._key,
          label: p.code || p._key,
        }));
    }
  } catch (error) {
    console.error('Error loading positions:', error);
    items.value = [];
    positionTreeNodes.value = [];
  }
}

async function createSession() {
  if (!sessionData.type) {
    Notify.create({
      type: 'negative',
      message: $t('warehouse.counting.type_required'),
      color: 'theme-red',
    });
    return;
  }

  if (assignments.value.length === 0) {
    Notify.create({
      type: 'negative',
      message: $t('warehouse.counting.assignments_required'),
      color: 'theme-red',
    });
    return;
  }

  saving.value = true;

  try {
    // Create session
    const sessionPayload = {
      code: sessionData.code || null, // null for auto-generation
      description: sessionData.description || null,
      type: sessionData.type,
      blind_mode: sessionData.blind_mode,
      scheduled_start: sessionData.scheduled_start || null,
      scheduled_end: sessionData.scheduled_end || null,
    };

    const { data: sessionResponse } = await api.post(
      '/inventory/count-session',
      sessionPayload,
    );
    const sessionKey = sessionResponse.detail.counting_session_key;

    // Create assignments
    const assignmentPayloads = [];
    assignments.value.forEach((assignment) => {
      assignment.items?.forEach((item) => {
        assignmentPayloads.push({
          inventory_count_session_key: sessionKey,
          assignment_type: sessionData.type,
          product_key:
            sessionData.type === 'product' ? item._key : null,
          position_key:
            sessionData.type === 'position' ? (item._key || item.key) : null,
        });
      });
    });

    if (assignmentPayloads.length > 0) {
      await api.post('/inventory/count-assignment', assignmentPayloads);
    }

    Notify.create({
      type: 'positive',
      message: $t('warehouse.counting.session.created_successfully'),
      color: 'theme-green',
    });

    onDialogOK();
  } catch (error) {
    console.error('Error creating session:', error);
    Notify.create({
      type: 'negative',
      message: error.response?.data?.detail || $t('warehouse.counting.session.creation_error'),
      color: 'theme-red',
    });
  } finally {
    saving.value = false;
  }
}

function blur() {
  document.activeElement.blur();
}

// Load data on mount
onMounted(() => {
  store.dispatch('loadUsers');
  loadItems();
});

// Watch session type to reload appropriate data and reset state
watch(
  () => sessionData.type,
  () => {
    // Reset items and tree nodes
    items.value = [];
    positionTreeNodes.value = [];
    // Clear assignments when type changes
    assignments.value = [];
    selectedAssignment.value = null;
    // Load new items for the selected type
    loadItems();
  },
);
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
