<template>
  <div ref="container" class="q-px-sm q-pt-sm full-height">
    <q-table
      id="serial_list"
      v-model:pagination="pagination"
      :columns="columns"
      :rows="serial_list"
      row-key="_key"
      :loading="loading"
      color="primary"
      hide-bottom
      class="full-height"
      dense
      separator="none"
      table-class="text-high"
      card-class="background no-shadow"
      virtual-scroll
      binary-state-sort
      :virtual-scroll-item-size="48"
      :virtual-scroll-sticky-size-start="48"
      :rows-per-page-options="[0]"
      @virtual-scroll="(details) => $emit('onScroll', details)"
      @request="
        (props) => {
          onRequest(props);
          $emit('onRequest', props);
        }
      "
    >
      <template #body="props">
        <q-tr
          :id="props.row._key"
          :key="props.row._key"
          :props="props"
          :style="props.row.closed ? 'opacity: .5' : ''"
          @dblclick="showSerialDetails(props.row._key)"
        >
          <template v-for="column in columns" :key="column.name">
            <q-td class="ellipsis" :props="props">
              <template v-if="column.format">
                {{
                  column.format(
                    (val = props.row[column.name]),
                    (row = props.row),
                  )
                }}
              </template>

              <template v-else>
                {{ $capitalizeAll(props.row[column.name] || '-') }}
              </template>
            </q-td>
          </template>
        </q-tr>
      </template>
    </q-table>
  </div>
</template>

<script>
import { ref } from 'vue';
import { useSerialColumns } from '@/composables/traceability';

export default {
  name: 'SerialsOverview',

  props: {
    loading: {
      type: Boolean,
      default: false,
    },
  },

  emits: ['onScroll', 'onRequest'],

  setup() {
    const pagination = ref({
      rowsPerPage: 0,
      sortBy: 'created',
      descending: false,
      page: 1,
      rowsNumber: 1000,
    });

    function onRequest(props) {
      const { page, rowsPerPage, sortBy, descending } = props.pagination;
      pagination.value.descending = descending;
      pagination.value.sortBy = sortBy;
      pagination.value.page = page;
      pagination.value.rowsPerPage = rowsPerPage;
    }

    const serialColumns = useSerialColumns();

    return {
      pagination,
      onRequest,
      serialColumns,
    };
  },

  data() {
    return {
      table_height: '80vh',
    };
  },

  computed: {
    serial_list() {
      return this.$store.state.serial.serials;
    },

    columns() {
      return this.serialColumns;
    },
  },

  methods: {
    getValueFromField(fieldValue) {
      if (!fieldValue) {
        return '---';
      } else if (fieldValue instanceof Object) {
        return fieldValue.value;
      }
      return fieldValue;
    },

    customFieldValue(row, key) {
      let returnValue = '---';
      if (row && row['grid_data']) {
        row['grid_data'].forEach((field) => {
          if (field._key === key) {
            returnValue = this.getValueFromField(field.value);
          }
        });
      }
      return returnValue;
    },

    showSerialDetails(serialKey) {
      const to_route = {
        name: 'serialDetail',
        params: { serialKey },
        query: {
          back_to: this.$route.name,
          ...this.$route.query,
        },
      };
      this.$router.push(to_route);
    },
  },
};
</script>

<style lang="sass">
#serial_list
  & th
    font-weight: bold
    color: var(--text-low)
    border-bottom: 1px solid #fff2
  & td
    font-size: 14px
    padding-top: 8px
    padding-bottom: 8px

  .q-table__top,
  .q-table__bottom,
  thead tr:first-child th /* bg color is important for th; just specify one */
    background-color: var(--bg-color)

  thead
    position: sticky
    z-index: 1
    top: 0
</style>
