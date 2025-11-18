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
        <CountSessionDataTab
          :session-data="sessionData"
          @update:session-data="sessionData = $event"
        />
        </q-tab-panel>
        <!-- TAB 2: ASSIGNMENTS -->
        <q-tab-panel :name="2">
        <CountSessionAssignmentsTab
          ref="assignmentsTabRef"
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
        </div>
      </q-card-section>
    </q-card>
  </BaseDialog>
</template>

<script setup>
import { useDialogPluginComponent } from 'quasar';
import { ref, watch, onMounted, reactive } from 'vue';
import { useI18n } from 'vue-i18n';
import { useStore } from 'vuex';
import { api } from '@/boot/axios';
import { Notify } from 'quasar';
import BaseDialog from '@/components/BaseDialog.vue';
import CountSessionDataTab from './CountSessionDataTab.vue';
import CountSessionAssignmentsTab from './CountSessionAssignmentsTab.vue';

const props = defineProps({});

defineEmits(useDialogPluginComponent.emitsObject);

const { dialogRef, onDialogHide, onDialogOK, onDialogCancel } = useDialogPluginComponent();
const getDialogRef = () => dialogRef;

const { t: $t } = useI18n();
const store = useStore();

const step = ref(1);
const saving = ref(false);
const disableAssignedItems = ref(false);
const assignmentsTabRef = ref(null);

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

// Methods

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

  // Get assignments from the child component
  const assignments = assignmentsTabRef.value?.assignments || [];

  if (assignments.length === 0) {
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

    onDialogOK();
  } catch (error) {
    console.error('Error creating session:', error);
    Notify.create({
      type: 'negative',
      // message: error.response?.data?.detail || $t('warehouse.counting.session.creation_error'),
      message: $t('warehouse.counting.session.creation_error'),
      color: 'theme-red',
      timeout: 0,
      actions: [{ label: 'CLOSE', color: 'white', handler: () => {} }],
    });
  } finally {
    saving.value = false;
  }
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
    if (assignmentsTabRef.value) {
      assignmentsTabRef.value.assignments = [];
      assignmentsTabRef.value.selectedAssignment = null;
    }
    // Load new items for the selected type
    loadItems();
  },
);
</script>
