<template>
    <q-table
      id="wo_field_data"
      :columns="columns"
      :rows="filtered_serials_list"
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
                      :class="{'text-strike text-italic text-low': !props.row.serial_field_value.some((f) => f.name === file.name)}"
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
                  {{ $capitalizeAll(props.row[column.name] || '') }}
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

<script>
import { formatDateTime } from '@/lib/TimeHandling';
import { mapState } from 'vuex';
import MediaViewer from '@/components/MediaViewer.vue';

export default {
  name: 'WorkOrderTraceabilityData',

  components: {
    MediaViewer,
  },

  props: {
    filters: {
      type: Object,
      required: true,
      default: () => {
        return {
          phase_alias: '',
          serial: '',
          operator_key: '',
          job_selected: '',
          field_selected: '',
        };
      },
    },
    wo_field_data: {
      type: Object,
      required: true,
    },
  },

  data() {
    return {
      show_media: undefined,
      table_height: '80vh',
      table_header_style: {
        borderBottom: '3px solid green',
        fontWeight: 'bold',
        borderCollapse: 'separate',
      },
      search_fields: [],
      temp_date: null,
      change_sequence_for_wo: null,
      now: new Date(),
    };
  },

  computed: {
    ...mapState({
      wo_key: (state) => state.workorder.wo_data._key,
      traceability_level: (state) => state.workorder.wo_data.traceability_level,
    }),

    columns() {
      const baseColumns = [
        {
          field: 'job_key',
          name: 'job_key',
          sortable: true,
          label: this.$t('job').toUpperCase(),
          align: 'left',
        },
        {
          field: 'user',
          name: 'operator_username',
          sortable: true,
          label: this.$t('operator').toUpperCase(),
          align: 'left',
          style: 'max-width: 10vw',
        },
        {
          field: 'phase_alias',
          name: 'phase_alias',
          sortable: true,
          label: this.$t('phase').toUpperCase(),
          style: 'max-width: 10vw',
          align: 'left',
        },
        {
          field: 'field_label',
          name: 'field_label',
          sortable: true,
          label: this.$t('field').toUpperCase(),
          align: 'left',
        },
        {
          field: 'step_field_value',
          name: 'value',
          sortable: true,
          label: this.$t('value').toUpperCase(),
          align: 'left',
        },
        {
          field: 'timestamp',
          sortable: true,
          name: 'timestamp',
          align: 'right',
          label: this.$t('timestamp').toUpperCase(),
        },
      ];

      return this.traceability_level
        ? [{
          field: 'serial_code',
          name: 'serial_code',
          sortable: true,
          label: this.$t('serial').toUpperCase(),
          style: 'max-width: 10vw',
          align: 'left',
        }, ...baseColumns]
        : [{
          field: 'batch_key',
          name: 'batch_key',
          sortable: true,
          label: this.$t('batch').toUpperCase(),
          align: 'left',
          style: 'max-width: 10vw',
        }, ...baseColumns];
    },

    filtered_serials_list() {
      return this.wo_field_data.filter((serial) => {
        /*
        Initialize filter results.
        If any false will be found in this array the filter function will return false
        */
        let filter_match_map = [];
        this.search_fields = [];

        for (const [filter, value] of Object.entries(this.filters)) {
          // by default show wo in the list
          let match = true;

          switch (filter) {
            case 'phase_alias':
              if (value && serial.phase_key !== value) {
                match = false;
              }
              break;

            case 'serial':
              if (value && serial.serial_key !== value) {
                match = false;
              }
              break;

            case 'operator_key':
              if (value && serial.created_by !== value) {
                match = false;
              }
              break;

            case 'job_selected':
              if (value && serial.job_key !== value) {
                match = false;
              }
              break;

            case 'field_selected':
              if (value && serial.custom_field_key !== value) {
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
    },
  },

  methods: {
    goToSerial(serial_key) {
      this.$router.push({
        name: 'serialDetail',
        params: {
          serialKey: serial_key,
        }
      });
    },

    formatTimestamp(timestamp) {
      return formatDateTime(timestamp, this.$i18n.locale, {
        year: '2-digit',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    },

    getFieldValue(field_type, value) {
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
    },

    showMedia(field_data, file_name) {
      this.show_media = `/media/traceability/${this.wo_key}/${field_data.batch_key}/${field_data.step_key}/${field_data.custom_field_key}/${field_data.form_field_key}/${file_name}`
    },

    isOverridden(row) {
      return row.field_type === 'choice' ? row.serial_field_value.value !== row.value.value : row.serial_field_value !== row.value;
    },

    fieldFiles(row) {
      const total_files = new Set([...row.value.map((f) => f.name), ...row.serial_field_value.map((f) => f.name)]);
      return Array.from(total_files).map((filename) => {
        return {
          name: filename,
          new: !row.value.some((f) => f.name === filename),
          overridden: !row.serial_field_value.some((f) => f.name === filename),
        };
      });
    }
  },
};
</script>

<style lang="sass" scoped>
.link
  cursor: pointer
  &:hover
    text-decoration: underline
</style>