<template>
  <BaseDialog :show="true" @close.stop="router.back()">
    <q-card class="surface1 column" style="height: 90vh; min-width: 90vw">
      <q-card-section class="row items-center justify-between col-auto q-pb-none">
        <div class="display text-h3">
          {{ isEditMode ? $t('warehouse.counting.session_edit') : $t('warehouse.counting.session_new') }}
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

      <q-linear-progress v-if="loading" indeterminate color="primary" />

      <q-tab-panels
        v-model="step"
        class="col surface1"
      >
        <!-- TAB 1: SESSION DATA -->
        <q-tab-panel :name="1" class="q-px-none">
          <CountSessionDataTab
            v-model:session-data="sessionData"
            :session-status="sessionData.status || 'planned'"
          />
        </q-tab-panel>
        <!-- TAB 2: ASSIGNMENTS -->
        <q-tab-panel :name="2" class="q-px-none">
          <CountSessionAssignmentsTab
            v-model:assignments="assignments"
            :session-type="sessionData.type"
            :items="items"
            :position-tree-nodes="positionTreeNodes"
            :disable-assigned-items="disableAssignedItems"
          />
        </q-tab-panel>
      </q-tab-panels>

      <q-separator />

      <q-card-section class="col-auto">
        <div class="row items-center q-gutter-x-sm justify-between">
          <div class="col-auto">
            <q-checkbox
              v-if="step === 2"
              v-model="disableAssignedItems"
              :label="$t('warehouse.counting.disable_assigned_items')"
              dense
            />
          </div>
          <div class="row items-center q-gutter-x-sm">
            <q-btn
              :label="$t('cancel')"
              color="theme-grey"
              @click="router.back()"
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
              :label="isEditMode ? $t('save') : $t('create')"
              color="primary"
              :loading="saving"
              @click="saveSession"
            />
          </div>
        </div>
      </q-card-section>
    </q-card>
  </BaseDialog>
</template>

<script setup>
import { ref, watch, onMounted, reactive, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { useStore } from 'vuex';
import { api } from '@/boot/axios';
import { Notify } from 'quasar';
import BaseDialog from '@/components/BaseDialog.vue';
import CountSessionDataTab from './CountSessionDataTab.vue';
import CountSessionAssignmentsTab from './CountSessionAssignmentsTab.vue';

const props = defineProps({
  countSessionKey: {
    type: String,
    default: null,
  },
});

const { t: $t } = useI18n();
const store = useStore();
const router = useRouter();
const step = ref(1);
const saving = ref(false);
const loading = ref(false);
const disableAssignedItems = ref(false);
const isEditMode = computed(() => !!props.countSessionKey);
const originalSessionType = ref(null);

const sessionData = reactive({
  code: '',
  description: '',
  type: 'product', // 'product' or 'position'
  blind_mode: true,
  scheduled_start: null,
  scheduled_end: null,
});

const items = ref([]); // Unified list: products or positions depending on type
const positionTreeNodes = ref([]);
const assignments = ref([]); // Store assignments for v-model binding
const initialAssignments = ref(new Map()); // Map of assignment key -> status

// Methods

async function loadSessionData() {
  if (!props.countSessionKey) return;

  loading.value = true;
  try {
    // Fetch session data
    const { data } = await api.get(`/inventory/count-session/${props.countSessionKey}`);

    // Update session data (destructure session fields)
    Object.assign(sessionData, {
      code: data.code,
      description: data.description,
      type: data.type,
      blind_mode: data.blind_mode,
      scheduled_start: data.scheduled_start,
      scheduled_end: data.scheduled_end,
      status: data.status,
    });

    originalSessionType.value = data.type;

    // Load items for the session type
    await loadItems();

    // Process assignments - backend returns { [user_key]: [{ target_key, status, target_data }] }
    const assignmentsByUser = [];
    const loadedAssignments = new Map();

    if (data.assignments) {
      for (const [userKey, userAssignments] of Object.entries(data.assignments)) {
        const assignment = {
          user_key: userKey,
          items: [],
        };

        // Convert backend assignment format to minimal item structure
        for (const assign of userAssignments) {
          if (assign._key) {
            loadedAssignments.set(assign._key, assign.status);
          }
          assignment.items.push({
            _key: data.type === 'product' ? assign.target_key : undefined,
            key: data.type === 'position' ? assign.target_key : undefined,
            assignment_key: assign._key,
            code: assign.target_data?.code || assign.target_key,
            description: assign.target_data?.description || undefined,
            assignment_status: assign.status,
          });
        }

        assignmentsByUser.push(assignment);
      }
    }

    // Set assignments - v-model will automatically sync to child component when it mounts
    assignments.value = assignmentsByUser;
    initialAssignments.value = loadedAssignments;

  } catch (error) {
    console.error('Error loading session data:', error);
    Notify.create({
      type: 'negative',
      message: $t('warehouse.counting.session.load_error'),
      color: 'theme-red',
    });
  } finally {
    loading.value = false;
  }
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

async function updateSession(assignments) {

  const sessionPayload = {};
  ['code', 'description', 'type', 'blind_mode', 'scheduled_start', 'scheduled_end'].forEach(field => {
    if (sessionData[field] !== undefined) {
      sessionPayload[field] = sessionData[field];
    }
  });

  await api.put(`/inventory/count-session/${props.countSessionKey}`, sessionPayload);

  // Manage assignments
  // Use initialAssignments to determine additions and deletions
  const assignmentsToDelete = [];
  const remainingKeys = new Set(initialAssignments.value.keys());
  const newAssignments = [];

  for (const assignment of assignments) {
    for (const item of assignment.items) {
      // Check if this assignment has a key (meaning it existed)
      if (item.assignment_key) {
        if (remainingKeys.has(item.assignment_key)) {
          // Still exists, so remove from deletion set (mark as kept)
          remainingKeys.delete(item.assignment_key);
        }
      } else {
        // New assignment
        newAssignments.push({
          inventory_count_session_key: props.countSessionKey,
          assigned_to: assignment.user_key,
          target_key: item._key || item.key,
          target_type: sessionData.type,
        });
      }
    }
  }

  // Identify assignments to delete (only if they were 'planned')
  for (const key of remainingKeys) {
    if (initialAssignments.value.get(key) === 'planned') {
      assignmentsToDelete.push(key);
    }
  }

  if (assignmentsToDelete.length > 0) {
    await api.delete('/inventory/count-assignment', {
      data: { assignment_keys: assignmentsToDelete },
    });
  }

  // Add new assignments
  if (newAssignments.length > 0) {
    await api.post('/inventory/count-assignment', newAssignments);
  }

  Notify.create({
    message: $t('warehouse.counting.session.updated_successfully'),
    color: 'theme-green',
  });
}

async function createSession(assignments) {
  const sessionPayload = {
    code: sessionData.code || null, // null for auto-generation
    description: sessionData.description || null,
    type: sessionData.type,
    blind_mode: sessionData.blind_mode,
    scheduled_start: sessionData.scheduled_start || null,
    scheduled_end: sessionData.scheduled_end || null,
  };

  // Create assignments
  const assignmentPayloads = assignments.map((assignment) => ({
    user_key: assignment.user_key,
    target_keys: assignment.items.map((item) => item._key || item.key),
  }));

  const { data: sessionResponse } = await api.post(
    '/inventory/count-session', {
      count_session: sessionPayload,
      assignments: assignmentPayloads,
    }
  );

  Notify.create({
    message: $t('warehouse.counting.session.created_successfully'),
    color: 'theme-green',
  });
}

async function saveSession() {
  if (!sessionData.type) {
    Notify.create({
      type: 'negative',
      message: $t('warehouse.counting.type_required'),
      color: 'theme-red',
    });
    return;
  }

  // Get assignments from the reactive ref
  const currentAssignments = assignments.value || [];



  saving.value = true;

  try {
    if (isEditMode.value) {
      await updateSession(currentAssignments);
    } else {
      await createSession(currentAssignments);
    }
    await store.dispatch('getCountSessions');
    router.back();
  } catch (error) {
    console.error('Error saving session:', error);
    Notify.create({
      type: 'negative',
      message: error.response?.data?.detail || (isEditMode.value
        ? $t('warehouse.counting.session.update_error')
        : $t('warehouse.counting.session.creation_error')),
      color: 'theme-red',
      timeout: 0,
      actions: [{ label: 'CLOSE', color: 'white', handler: () => {} }],
    });
  } finally {
    saving.value = false;
  }
}

// Load data on mount
onMounted(async () => {
  store.dispatch('loadUsers');

  if (isEditMode.value) {
    // Load session and assignment data
    await loadSessionData();
  } else {
    // Just load items for create mode
    await loadItems();
  }
});

// Watch session type to reload appropriate data and reset state
watch(
  () => sessionData.type,
  async (newType, oldType) => {
    // Only react if type actually changed
    if (newType === oldType) return;

    // In edit mode, warn about type changes
    if (isEditMode.value && originalSessionType.value && newType !== originalSessionType.value) {
      // Show confirmation dialog
      const confirmed = await new Promise((resolve) => {
        Notify.create({
          message: $t('warehouse.counting.type_change_warning'),
          color: 'theme-orange',
          timeout: 0,
          actions: [
            { label: $t('cancel'), color: 'white', handler: () => resolve(false) },
            { label: $t('confirm'), color: 'white', handler: () => resolve(true) },
          ],
        });
      });

      if (!confirmed) {
        // Revert the type change
        sessionData.type = oldType;
        return;
      }

      // Delete existing assignments
      try {
        loading.value = true;
        // Collect all planned assignment keys from initialAssignments
        const assignmentKeys = [];
        for (const [key, status] of initialAssignments.value.entries()) {
            if (status === 'planned') {
                assignmentKeys.push(key);
            }
        }

        if (assignmentKeys.length > 0) {
          await api.delete('/inventory/count-assignment', {
            data: { assignment_keys: assignmentKeys },
          });
        }
      } catch (error) {
        console.error('Error deleting assignments:', error);
        Notify.create({
          type: 'negative',
          message: $t('warehouse.counting.session.delete_assignments_error'),
          color: 'theme-red',
        });
        sessionData.type = oldType;
        loading.value = false;
        return;
      } finally {
        loading.value = false;
      }
    }

    // Reset items and tree nodes
    items.value = [];
    positionTreeNodes.value = [];

    // Clear assignments when type changes
    assignments.value = [];

    // Load new items for the selected type
    await loadItems();
  }
);
</script>
