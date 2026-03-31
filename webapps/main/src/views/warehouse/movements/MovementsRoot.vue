<template>
  <div ref="container" class="q-px-sm q-pt-sm full-height">
    <q-table
      id="movement_list"
      v-model:pagination="pagination"
      :columns="columns"
      :rows="movement_list"
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
      :virtual-scroll-item-size="48"
      :virtual-scroll-sticky-size-start="48"
      :rows-per-page-options="[0]"
      @virtual-scroll="addMovements"
      @request="reloadMovements"
    >
      <template #body="props">
        <q-tr
          :id="props.row._key"
          :key="props.row._key"
          :props="props"
          @dblclick="showMovementDetails(props.row._key)"
        >

          <!-- Movement reversal context menu -->
          <q-popup-proxy context-menu>

            <div class="q-pa-md ">
              <div class="text-h4 highlight">
                {{ $t('warehouse.movement.label') }} {{ props.row._key }}
              </div>
              <div v-if="props.row.reason !== null" class="q-mt-md">
                {{ props.row.reason }}
              </div>
            </div>


            <q-separator />

            <q-list dense>
              <template v-if="isReversible(props.row)">
                <q-item clickable class="text-theme-blue" @click="handleContextMenuClick(props.row)">
                  <q-item-section side >
                    <q-item-label>
                      <q-icon name="mdi-undo-variant" size="xs" :color="props.row.inverse_movement_key ? 'text-high' : 'theme-blue'"/>
                    </q-item-label>
                  </q-item-section>
                  <q-item-section class="text-uppercase" :class="props.row.inverse_movement_key ? 'text-high' : 'theme-blue'">
                    <q-item-label v-if="!props.row.inverse_movement_key">
                      {{ $t('revert_movement') }}
                    </q-item-label>
                    <template v-else>
                      <q-item-label>{{ $t('movement_reverted_by', { key: props.row.inverse_movement_key }) }}</q-item-label>
                      <q-item-label caption class="text-low smaller">(Click to copy canceled movement key)</q-item-label>
                    </template>
                  </q-item-section>
                </q-item>
                <q-separator />
              </template>

              <template v-if="Object.values(props.row.references).filter(ref => ref !== null).length > 0">
                <q-item-label header>Riferimenti</q-item-label>

                <q-item v-for="[ref_type, ref_key] in Object.entries(props.row.references).filter(([_, ref]) => ref !== null)" :key="ref_type">
                  <q-item-section>
                    <q-item-label class="text-uppercase text-h6 weight-bold text-low">
                      {{ ref_type }}
                    </q-item-label>
                  </q-item-section>
                  <q-item-section side>
                    <q-item-label class="weight-bold">
                      {{ ref_key || '-' }}
                    </q-item-label>
                  </q-item-section>
                </q-item>
              </template>
            </q-list>

          </q-popup-proxy>

          <!-- Movement details -->
          <template v-for="column in columns" :key="column.name">
            <q-td class="ellipsis" :props="props">
              <template
                v-if="['created', 'start', 'end'].includes(column.name)"
              >
                <span>
                  {{
                    props.row[column.name] === null
                    ? '-'
                    : $shortDateString(props.row[column.name], $i18n.locale)
                  }}
                  <q-tooltip :delay="500" self="bottom middle" anchor="top middle">
                    {{ props.row[column.name].slice(11, 19) }}
                  </q-tooltip>
                </span>
              </template>

              <template v-else-if="column.name === 'type'">
                <q-icon :name="typeIconMap[props.row.type]" size="xs"/>
              </template>

              <template v-else-if="column.name === 'status'">
                <q-icon :name="statusIconMap[props.row.status]" size="15px"/>
                <q-icon v-if="props.row.inverse_movement_key" name="mdi-undo-variant" size="xs"/>
              </template>

              <template v-else-if="column.name === 'quantity'">
                {{ roundQuantity(props.row.qt_confirmed) }} / {{ roundQuantity(props.row.qt_planned) }}
              </template>

              <template v-else-if="column.name === 'user'">
                <BaseUserAvatar
                  :show_name="false"
                  :user="props.row.user" size="24px">
                </BaseUserAvatar>
                <q-tooltip anchor="top middle" self="bottom middle" delay="500" :offset="[10, 0]">
                  {{ props.row.user.name }} {{ props.row.user.surname }}
                </q-tooltip>
              </template>

              <template v-else-if="column.name === 'position_from_code'">
                <span :class="{ 'text-strike text-low': props.row.position_from_deleted }">
                  {{ $capitalizeAll(props.row.position_from_code || '-') }}
                </span>
                <q-tooltip v-if="props.row.position_from_deleted" anchor="top middle" self="bottom middle" :delay="300">
                  {{ $t('position_deleted') }}
                </q-tooltip>
              </template>

              <template v-else-if="column.name === 'position_to_code'">
                <span :class="{ 'text-strike text-low': props.row.position_to_deleted }">
                  {{ $capitalizeAll(props.row.position_to_code || '-') }}
                </span>
                <q-tooltip v-if="props.row.position_to_deleted" anchor="top middle" self="bottom middle" :delay="300">
                  {{ $t('position_deleted') }}
                </q-tooltip>
              </template>

              <template v-else>
                {{ $capitalizeAll(props.row[column.field] || '-') }}
              </template>
            </q-td>
          </template>
        </q-tr>
      </template>
    </q-table>

    <BasePrompt
      :show="revert_movement_key !== null"
      width="40%"
      :prompt="$t('revert_movement', { key: revert_movement_key })"
      :help-text="$t('movement_revert_reason_help')"
      @update="(reason) => revertMovement(reason)"
      @close="revert_movement_key = null"
    />
  </div>
</template>

<script>
import { ref } from 'vue';
import BasePrompt from '@/components/BasePrompt.vue';
import BaseUserAvatar from '@/components/BaseUserAvatar.vue';
import queryModel from '@/lib/queryModelFactory.js';
import { sendEvent } from '@/composables/event.js';
import { useMovementColumns } from 'app/src/composables/warehouse';
import { useSSE } from '@/composables/useSSE';

export default {
  name: 'MovementsRoot',

  components: {
    BasePrompt,
    BaseUserAvatar
  },


  setup() {
    const pagination = ref({
      rowsPerPage: 0,
      sortBy: 'created',
      descending: false,
      page: 1,
      rowsNumber: 1000,
    });

    const typeIconMap = {
      'receipt': 'mdi-import',
      'transfer': 'mdi-swap-horizontal',
      'shipment': 'mdi-export',
      'adjustment': 'mdi-plus-minus-variant',
      'production': 'mdi-package-variant-closed-plus',
      'consumption': 'mdi-package-variant-closed-minus',
      'reversal': 'mdi-undo-variant'
    }

    const statusIconMap = {
      'completed': 'mdi-check-circle-outline',
      'started': 'mdi-progress-helper',
      'planned': 'mdi-calendar-clock-outline'
    }

    const movementColumns = useMovementColumns();
    const { subscribe } = useSSE('inventory-notification');

    return {
      pagination,
      movementColumns,
      typeIconMap,
      statusIconMap,
      subscribeSSE: subscribe,
    };
  },

  data() {
    return {
      loading: false,
      loading_fields: false,
      limit: 200,
      offset: 0,
      revert_movement_key: null
    };
  },

  computed: {
    product_search: queryModel(String, 'product_search', null),
    position_from: queryModel(String, 'position_from', null),
    position_to: queryModel(String, 'position_to', null),
    search_graph: queryModel(Boolean, 'search_graph', true),

    positionFilterOperator: queryModel(
      String,
      'position_filter_operator',
      'AND',
    ),

    movement_type: queryModel(String, 'movement_type', null),
    movement_status: queryModel(String, 'movement_status', null),

    start_from: queryModel(String, 'start_from', null),
    start_to: queryModel(String, 'start_to', null),
    end_from: queryModel(String, 'end_from', null),
    end_to: queryModel(String, 'end_to', null),

    serial_search: queryModel(String, 'serial_search', null),
    work_order_search: queryModel(String, 'work_order_search', null),
    list_search: queryModel(String, 'list_search', null),

    filters() {
      return {
        position_from: this.position_from,
        position_to: this.position_to,
        position_filter_operator: this.positionFilterOperator,
        search_graph: this.search_graph,

        movement_type: this.movement_type,
        movement_status: this.movement_status,
        start_from: this.start_from ? this.formatDate(this.start_from) : null,
        start_to: this.start_to ? this.formatDate(this.start_to, true) : null,
        end_from: this.end_from ? this.formatDate(this.end_from) : null,
        end_to: this.end_to ? this.formatDate(this.end_to, true) : null,

        product_search: this.product_search,
        serial_search: this.serial_search,
        work_order_search: this.work_order_search,
        list_search: this.list_search,
      };
    },

    movement_list() {
      return this.$store.state.warehouse.movements.map(movement => ({
        ...movement,
        user: this.getUser(movement.user_key)
      }));
    },

    columns() {
      return this.movementColumns;
    },
  },

  watch: {
    filters: {
      deep: true,
      handler: 'getMovements',
    },
  },

  created() {
    this.getMovements();
    this.$store.dispatch('loadUsers');
  },

  mounted() {
    this.subscribeSSE((event) => {
      this.handleMessage(event);
    });
  },

  methods: {
    handleMessage(message) {
      this.refreshMovements();
      let event = JSON.parse(message.data);
      if (event.notification === 'ERROR') {
        this.$q.notify({
          message: this.getErrorMessage(event.error_code, event.error),
          color: 'theme-red',
          timeout: 1500,
          movement: 'top',
        });
      }
    },

    handleContextMenuClick(movement) {
      if (!movement.inverse_movement_key) {
        this.revert_movement_key = movement._key;
      }
      else {
        navigator.clipboard.writeText(movement.inverse_movement_key);
        this.$q.notify({
          message: 'movimento copiato',
          color: 'theme-green',
          position: 'top',
          timeout: 1500
        })
      }
    },

    isReversible(movement) {
      const isContainerTransfer = movement.type === 'transfer' && movement.product_key === null;
      return movement.qt_confirmed !== 0 && movement.type !== 'reversal' && !isContainerTransfer;
    },

    async revertMovement(reason) {
      try {
        await sendEvent({
          event_type: 'MOVEMENT_REVERSED',
          event_data: {
            original_movement_key: this.revert_movement_key,
            reason
          }
        });

        this.$q.notify({
          message: this.$t('movement.revert_success'),
          color: 'theme-green',
          position: 'top',
          timeout: 1500
        });
        this.revert_movement_key = null;
        this.refreshMovements();
      } catch (error) {
        this.$q.notify({
          message: error.response?.data?.message || this.$t('movement.revert_error'),
          color: 'theme-orange',
          position: 'top',
          timeout: 0,
          actions: [
            { label: 'Close', textColor: 'white', handler: () => undefined }
          ]
        });
      }
    },

    formatDate(date, endOfDay = false) {
      const formattedDate = new Date(date);
      if (endOfDay) {
        formattedDate.setHours(23, 59, 59, 999);
      }
      return formattedDate.toISOString();
    },

    refreshMovements() {
      this.getMovements();
    },

    getMovements() {
      this.reloadMovements({ pagination: this.pagination });
    },

    getUser(userKey) {
      const user = this.$store.getters.user_data(userKey);
      return user
    },

    showMovementDetails(movementKey) {
      const to_route = {
        name: 'movementDetail',
        params: { movementKey },
        query: {
          back_to: this.$route.name,
          ...this.$route.query,
        },
      };
      this.$router.push(to_route);
    },

    reloadMovements(data) {
      const { sortBy, descending } = data.pagination ?? {};

      this.sort_by = sortBy;
      this.sorting_order = descending ? 'desc' : 'asc';
      this.loading = true;
      this.$store
        .dispatch('getMovements', {
          ...this.filters,
          limit: this.offset + this.limit,
          offset: 0,
          sort_by: this.sort_by,
          sorting_order: this.sorting_order,
        })
        .then(() =>
          setTimeout(() => {
            this.loading = false;
          }, 1000),
        );
    },

    hasMore() {
      return this.limit + this.offset <= this.$store.getters.getMovementCount();
    },

    addMovements(data) {
      const lastIndex = this.$store.getters.getMovementCount() - 1;

      if (this.loading !== true && data.to === lastIndex && this.hasMore()) {
        this.offset += this.limit;
        this.loading = true;
        this.$store
          .dispatch('appendMovements', {
            ...this.filters,
            filter_unreleased: true,
            offset: this.offset,
            sort_by: this.sort_by,
            sorting_order: this.sorting_order,
          })
          .then(() =>
            setTimeout(() => {
              this.loading = false;
            }, 1000),
          );
      }
    },

    roundQuantity(value) {
      if (value === null || value === undefined) {
        return '-';
      }
      // Round to 4 decimal places to keep visualization stable
      return Math.round(value * 10 ** 4) / 10 ** 4;
    },
  },
};
</script>

<style lang="sass">
#movement_list
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

  thead tr th
    position: sticky
    z-index: 1
  thead tr:first-child th
    top: 0
</style>
