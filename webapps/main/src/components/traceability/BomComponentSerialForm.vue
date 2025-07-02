<template>
  <BaseDialog
    :show="show"
    @close="
      {
        saving = false;
        $emit('close');
      }
    "
  >
    <q-card
      square
      class="surface1 q-pa-md"
      style="min-width: 600px; max-width: 800px"
    >
        <!-- FORM TITLE -->
        <q-card-section class="column">
          <div class="text-h2 display highlight">
            {{ component_code }}
          </div>
          <div class="text-body1">
            {{ bom_line.component_description }}
          </div>
        </q-card-section>

        <NoDataAlert v-if="!batch_serials">
          {{ $t('serial_field.noData') }}
        </NoDataAlert>

        <q-card-section v-else class="column q-gutter-y-md">
          <template v-for="serial in batch_serials" :key="serial._id">
            <div class="row q-mb-md">
              <div class="col">
                <BaseAutocompleteSerial
                  :value="getLineSerials(serial._key)"
                  :label="
                    $capitalize(
                      [$t('serial'), serial?.code || serial._key].join(' '),
                    )
                  "
                  :hint="$t('serial_autocomplete_hint', { minChars: 3 })"
                  :product_key="component_key"
                  :loading="loading"
                  :can_create="true"
                  :selection_qt="bom_line.qt"
                  :filter_used="true"
                  :used-serials="usedSerialsKeys"
                  :inventory_only="bom_line.manage_inventory"
                  :inventory_in_position_key="bom_line?.consumption_options?.consumption_position_key"
                  @select="(selection) => emit('select', {selection, bomLine: props.bom_line, parentSerialKey: serial._key})"
                >
                </BaseAutocompleteSerial>
              </div>
            </div>
            <q-separator class="q-my-md" />
          </template>
        </q-card-section>

        <!-- FORM ACTIONS    navigation -->
        <q-card-section>
          <div class="row q-gutter-md">
            <q-btn
              v-if="batch_serials"
              color="theme-orange"
              :label="$t('save')"
              :loading="saving"
              @click="save"
            >
            </q-btn>

            <q-space />

            <q-btn color="theme-grey" :label="$t('cancel')" @click="cancel">
            </q-btn>
          </div>
        </q-card-section>
    </q-card>
  </BaseDialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { useStore } from 'vuex';
import { api } from '@/boot/axios';
import BaseAutocompleteSerial from '@/components/BaseAutocompleteSerial.vue';
import BaseDialog from '@/components/BaseDialog.vue';
import NoDataAlert from '@/components/NoDataAlert.vue';

const { t: $t } = useI18n();

// Props definition
const props = defineProps({
  show: {
    type: Boolean,
    default: true,
  },
  traceability_enabled: {
    type: Boolean,
    default: true,
  },
  bom_line: {
    type: Object,
    default: null,
  },
  batch_key: {
    type: String,
    default: null,
  },
  phase_key: {
    type: String,
    required: true,
  },
  wo_key: {
    type: String,
    required: true,
  },
  usedSerials: {
    type: Array,
    default: () => [],
  },
});

const emit = defineEmits(['close', 'select', 'reset']);

// Store setup
const store = useStore();

// Reactive state
const saving = ref(false);
const batch_serials = ref([]);
const loading = ref(false);

// Computed properties
const faked_batch_serials = computed(() => store.state.traceability.current_batch_faked_serials);
const component_code = computed(() => props.bom_line.component_code);
const component_key = computed(() => props.bom_line.component_key);

const serialLinks = computed(() => store.state.traceability.bom_serials);
const usedSerialsKeys = computed(() => serialLinks.value.map(serial => serial._key));


// Methods

// Get all output serials for the current batch
const getBatchSerials = async () => {
  if (!props.batch_key) {return};
  loading.value = true;
  const { data: serials } = await api.get('serial-batch', {
    params: { batch_key: props.batch_key },
  });
  batch_serials.value = serials;
  loading.value = false;
};

// Get all serials for the current bom line
function getLineSerials(parentSerialKey) {
  const lineLinks = serialLinks.value.filter(link =>
    link.phase_key == props.phase_key
    && link.component_key == component_key.value
    && link.batch_key == props.batch_key
    && link.parent_serial_key == parentSerialKey
  )
  // Return array of serial keys if qt > 1 (multiple selection),
  // otherwise return single serial key
  return props.bom_line.qt > 1
    ? lineLinks
    : lineLinks[0]
}


const fakeBatchSerials = async () => {
  loading.value = true;
  await store.dispatch('fakeBatchSerials', {
    batch_key: props.batch_key,
  });
  batch_serials.value = faked_batch_serials.value;
  loading.value = false;
};

const save = async () => {
  saving.value = true;
  await store.dispatch('saveSerialLinks')
  saving.value = false;
  emit('close');
};



const cancel = () => {
  emit('reset');
  emit('close');
};


/* ================================
WATCH
================================ */

// Watch
watch(() => props.show, () => {
  if (!props.show) {return};
  if (props.traceability_enabled) {
    getBatchSerials();
  } else {
    fakeBatchSerials();
  }
});
</script>
