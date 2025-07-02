<template>
    <q-table
      id="wo_field_data"
      :columns="columns"
      :rows="filtered_data"
      row-key="_key"
      virtual-scroll
      hide-bottom
      dense
      class="full-height"
      separator="none"
      table-class="text-high"
      card-class="surface1 no-shadow"
      :rows-per-page-options="[0]"
    >

      <template #body="props">
        <q-tr :id="props.row._key" :key="props.row._key" :props="props">
          <template v-for="column in columns" :key="column.name">
            <q-td
              :props="props"
              class="ellipsis"
              :class="{
                'filter-field': search_fields.includes(column.name),
                'link': column.name === 'serial_code',
              }"
              @click="() => column.name === 'serial_code' ? goToSerial(props.row.serial_key) : null"
            >
              <span>
                <!-- ================================ -->
                <!-- TABLE FIELDS -->
                <!-- ================================ -->

                <!-- Timestamp -->
                <template v-if="column.name === 'timestamp'">
                  {{ formatTimestamp(props.row.timestamp) }}
                </template>

                <!-- Value -->
                <template v-else-if="column.name === 'value'">

                  <!-- File field value -->
                  <template v-if="props.row.field_type === 'files'">
                    <div
                      v-for="file in props.row.value"
                      :key="file.name"
                      class="link"
                      :class="{'text-strike text-italic text-low': traceability_level ? false : !props.row.serial_field_value?.some((f) => f.name === file.name)}"
                      @click="showMedia(props.row, file.name)"
                    >
                      {{ file.name }}
                    </div>
                  </template>

                  <!-- Other field types value -->
                  <div v-else :class="{'text-strike text-italic text-low': isOverridden(props.row)}">
                    {{ getFieldValue(props.row.field_type, props.row.value) }}
                  </div>
                </template>

                <!-- Other fields -->
                <template v-else>
                  {{ props.row[column.name] }}
                </template>
              </span>

              <!-- ================================ -->
              <!-- BATCH QUANTITY -->
              <!-- ================================ -->

              <span v-if="!traceability_level && column.name === 'batch_key'" class="weight-bold text-low q-ml-sm">
                {{ props.row.batch_qt }}x
              </span>

              <!-- ================================ -->
              <!-- TOOLTIP -->
              <!-- Used to display full value in case of truncation and serial value in case of value override -->
              <!-- ================================ -->

              <q-tooltip
                :delay="500"
                anchor="top left"
                self="bottom left"
                :offset="[8, 6]"
                transition-show="fade"
                transition-hide="fade"
              >
                <!-- ================================ -->
                <!-- TOOLTIP FIELDS -->
                <!-- ================================ -->

                <!-- Value -->
                <template v-if="column.name === 'value'">

                  <!-- File field value -->
                  <template v-if="props.row.field_type === 'files'">
                    <div
                      v-for="file in fieldFiles(props.row)" :key="file.name"
                      :class="{
                        'text-strike text-italic text-low': file.overridden,
                        'highlight': file.new,
                      }"
                    >
                      <span>
                        {{ file.name }}
                      </span>
                      <span v-if="file.new" class="text-bold">
                        ({{ $t('new') }})
                      </span>
                    </div>
                  </template>

                  <!-- Other field types value -->
                  <template v-else>
                    <span>
                      {{ getFieldValue(props.row.field_type, props.row.value) }}
                    </span>
                    <span v-if="isOverridden(props.row) && traceability_level" class="highlight">
                      → {{ getFieldValue(props.row.field_type, props.row.serial_field_value) }}
                    </span>
                  </template>

                </template>

                <!-- Other fields -->
                <template v-else>
                  {{ capitalizeAll(props.row[column.name] || '') }}
                </template>
              </q-tooltip>

            </q-td>
          </template>
        </q-tr>
      </template>
    </q-table>
    <MediaViewer
      v-if="show_media !== undefined"
      :show="show_media !== undefined"
      :media_name="show_media.split('/').pop()"
      :media_src="show_media"
      @close="show_media = undefined"
    />
</template>

<script setup>
import { ref, computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRouter } from 'vue-router';
import { useStore } from 'vuex';
import MediaViewer from '@/components/MediaViewer.vue';
import { formatDateTime } from '@/lib/TimeHandling';

// Props
const props = defineProps({
  filters: {
    type: Object,
    required: true,
    default: () => {
      return {
        selectedPhase: '',
        selectedSerial: '',
        selectedOperator: '',
        selectedJob: '',
        selectedField: '',
      };
    },
  },
  wo_traceability_data: {
    type: Object,
    required: true,
  },
  view: {
    type: String,
    required: true,
  },
});

// Composables
const store = useStore();
const { t, locale } = useI18n();
const router = useRouter();

// Data
const show_media = ref(undefined);
const search_fields = ref([]);

// Store state
const wo_key = computed(() => store.state.workorder.wo_data._key);
const traceability_level = computed(() => store.state.workorder.wo_data.traceability_level);

// Computed
const operatorColumn = computed(() => ({
  field: 'user',
  name: 'operator_username',
  sortable: true,
  label: t('operator').toUpperCase(),
  align: 'right',
  style: 'max-width: 10vw',
}));

const timestampColumn = computed(() => ({
  field: 'timestamp',
  sortable: true,
  name: 'timestamp',
  align: 'left',
  label: t('timestamp').toUpperCase(),
}));

const stepColumns = computed(() => {
  const baseColumns = [
    {
      field: 'job_key',
      name: 'job_key',
      sortable: true,
      label: t('job').toUpperCase(),
      align: 'left',
    },
    {
      field: 'phase_alias',
      name: 'phase_alias',
      sortable: true,
      label: t('phase.phase').toUpperCase(),
      style: 'max-width: 10vw',
      align: 'left',
    },
    {
      field: 'step_title',
      name: 'step_title',
      sortable: true,
      label: t('phase.step').toUpperCase(),
      align: 'left',
    },
  ];

  const traceabilityColumn = traceability_level.value
    ? {
      field: 'serial_code',
      name: 'serial_code',
      sortable: true,
      label: t('serial').toUpperCase(),
      style: 'max-width: 10vw',
      align: 'left',
    }
    : {
      field: 'batch_key',
      name: 'batch_key',
      sortable: true,
      label: t('batch').toUpperCase(),
      align: 'left',
      style: 'max-width: 10vw',
    };

  return  [
    ...baseColumns,
    traceabilityColumn,
  ]
});

const fieldColumns = computed(() => [
  {
    field: 'field_label',
    name: 'field_label',
    sortable: true,
    label: t('field').toUpperCase(),
    align: 'left',
  },
  {
    field: 'step_field_value',
    name: 'value',
    sortable: true,
    label: t('value').toUpperCase(),
    align: 'left',
  },
]);

const columns = computed(() => {
  if (props.view === 'step') {
    return [
      timestampColumn.value,
      ...stepColumns.value,
      operatorColumn.value,
    ];
  }
  if (props.view === 'form') {
    return [
      timestampColumn.value,
      ...stepColumns.value,
      ...fieldColumns.value,
      operatorColumn.value,
    ];
  }
  return [];
});



const filtered_data = computed(() => {
  return props.wo_traceability_data.filter((field) => {
    /*
    Initialize filter results.
    If any false will be found in this array the filter function will return false
    */
    let filter_match_map = [];
    search_fields.value = [];

    for (const [filter, value] of Object.entries(props.filters)) {
      // by default show wo in the list
      let match = true;

      switch (filter) {
        case 'selectedPhase':
          if (value && field.phase_key !== value) {
            match = false;
          }
          break;

        case 'selectedSerial':
          if (value && field.serial_key !== value) {
            match = false;
          }
          break;

        case 'selectedOperator':
          if (value && field.operator_key !== value) {
            match = false;
          }
          break;

        case 'selectedJob':
          if (value && field.job_key !== value) {
            match = false;
          }
          break;

        case 'selectedField':
          if (value && field.form_field_key !== value) {
            match = false;
          }
          break;
      }

      // add result of the specific filter to the map
      filter_match_map.push(match);
    }

    // Return false and exclude wo from list if any filter returned false
    return filter_match_map.every((i) => i === true);
  });
});

// Methods
const goToSerial = (serial_key) => {
  router.push({
    name: 'serialDetail',
    params: {
      serialKey: serial_key,
    }
  });
};

const formatTimestamp = (timestamp) => {
  return formatDateTime(timestamp, locale.value, {
    year: '2-digit',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};

const getFieldValue = (field_type, value) => {
  if (!field_type) {
    return '';
  }
  if (['text', 'number', 'boolean', 'ternary', 'date', 'time'].includes(field_type)) {
    return value;
  }
  if (field_type === 'choice') {
    return value?.value;
  }
  if (field_type === 'files') {
    if (!value) {
      return '';
    }
    return Array.prototype.join.call(
      value?.map((file) => {
        return file.name;
      }),
      '\n',
    );
  }
  return '';
};

const showMedia = (field_data, file_name) => {
  show_media.value = `/media/traceability/${wo_key.value}/${field_data.batch_key}/${field_data.step_key}/${field_data.custom_field_key}/${field_data.form_field_key}/${file_name}`;
};

const isOverridden = (row) => {
  if (!traceability_level.value) {
    return false;
  }
  return row.field_type === 'choice' ? row.serial_field_value.value !== row.value.value : row.serial_field_value !== row.value;
};

const fieldFiles = (row) => {
  const total_files = new Set([...row.value.map((f) => f.name), ...row.serial_field_value.map((f) => f.name)]);
  return Array.from(total_files).map((filename) => {
    return {
      name: filename,
      new: !row.value.some((f) => f.name === filename),
      overridden: !row.serial_field_value.some((f) => f.name === filename),
    };
  });
};

// Helper function for capitalizing text (replacing $capitalizeAll)
const capitalizeAll = (text) => {
  return text.split(' ').map(word =>
    word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()
  ).join(' ');
};
</script>

<style lang="sass" scoped>
.link
  cursor: pointer
  &:hover
    text-decoration: underline
</style>