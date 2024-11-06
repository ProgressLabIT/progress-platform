<template>
  <div class="q-pa-lg">
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
      card-class="background no-shadow"
      :rows-per-page-options="[0]"
    >
      <template #header-cell-issue_count="props">
        <q-th :props="props">
          <q-icon name="mdi-flag" size="14px" />
        </q-th>
      </template>

      <template #body="props">
        <q-tr :id="props.row._key" :key="props.row._key" :props="props">
          <template v-for="column in columns" :key="column.name">
            <q-td
              :props="props"
              class="ellipsis"
              :class="{ 'filter-field': search_fields.includes(column.name) }"
            >
              <span @click="setSearch(column.name, props.row[column.name])">
                {{ props.row[column.name] }}
                <q-tooltip
                  :delay="500"
                  anchor="top left"
                  self="bottom left"
                  :offset="[8, 6]"
                  transition-show="fade"
                  transition-hide="fade"
                >
                  <template v-if="column.name === 'product_code'">
                    <div class="highlight">
                      {{ props.row.product_code }}
                    </div>
                    <div>
                      {{ props.row.product_description }}
                    </div>
                  </template>
                  <template v-else>
                    {{ $capitalizeAll(props.row[column.name] || '') }}
                  </template>
                </q-tooltip>
              </span>
            </q-td>
          </template>
        </q-tr>
      </template>
    </q-table>
  </div>
</template>

<script>
export default {
  name: 'WorkOrderTraceabilityData',

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
    columns() {
      return [
        {
          field: 'serial_code',
          name: 'serial_code',
          sortable: true,
          label: this.$t('serial').toUpperCase(),
          style: 'max-width: 10vw',
          align: 'left',
        },
        {
          field: 'job_key',
          name: 'job_key',
          sortable: true,
          label: this.$t('job').toUpperCase(),
          align: 'left',
        },
        {
          field: 'batch_key',
          name: 'batch_key',
          sortable: true,
          label: this.$t('batch').toUpperCase(),
          align: 'left',
          style: 'max-width: 10vw',
        },
        {
          field: 'user',
          name: 'user',
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
          field: 'custom_field_value',
          name: 'custom_field_value',
          sortable: true,
          label: this.$t('value').toUpperCase(),
          align: 'left',
        },
        {
          field: 'created',
          sortable: true,
          name: 'created',
          align: 'right',
          label: this.$t('timestamp').toUpperCase(),
          sort: this.sortDate,
        },
      ];
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
};
</script>
