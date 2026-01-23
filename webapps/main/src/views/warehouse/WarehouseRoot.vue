<template>
  <q-page-container class="absolute-full">
    <q-page class="row full-height">
      <div class="column col full-height">
        <div class="row col-auto items-center q-pl-xs q-pr-md q-py-sm">
          <!-- TAB LINKS -->
          <q-tabs
            class="transparent text-low"
            active-class="text-high weight-bold"
            align="left"
            shrink
            dense
            indicator-color="theme-blue"
          >
            <q-route-tab
              v-for="(view, index) in views"
              :key="index"
              :to="{ name: view.route_name, query: $route.query }"
              class="display"
            >
              {{ $t(`views.${view.route_name}`) }}
            </q-route-tab>
          </q-tabs>

          <q-space />

          <!-- POSITION BUTTONS -->
          <q-btn
            v-if="$route.name?.startsWith('position')"
            class="q-ml-sm"
            size="0.75rem"
            color="theme-blue"
            :label="$t('new')"
            @click="$router.push({ name: 'positionNew' })"
          >
          </q-btn>

          <!-- MOVEMENTS BUTTONS -->

          <!-- INVENTORY BUTTONS -->

          <!-- COUNTING BUTTONS -->
          <q-btn
            v-if="$route.name === 'countSessions'"
            class="q-ml-sm"
            size="0.75rem"
            color="theme-blue"
            :label="$t('new')"
            @click="$router.push({ name: 'countSessionNew' })"
          >
          </q-btn>

          <!-- EXPORT EXCEL -->
          <q-btn
            class="q-ml-sm"
            size="0.75rem"
            :label="$t('export')"
            color="theme-blue"
            @click="exportExcel"
          >
          </q-btn>

          <!-- FILTER BUTTONS -->
          <q-btn
            v-if="!showFilterDrawer"
            class="q-ml-sm"
            size="sm"
            round
            :color="filtersActiveNo > 0 ? 'theme-blue' : 'theme-grey'"
            icon="mdi-filter"
            @click="showFilterDrawer = true"
          >
            <q-badge
              v-if="filtersActiveNo > 0"
              floating
              rounded
              color="theme-red"
              :label="filtersActiveNo"
              size="4px"
              style="font-family: 'Red Hat Text'; font-size: 8px"
            />
          </q-btn>
        </div>

        <!-- MAIN CONTENT -->
        <div class="col relative-position">
          <router-view />
        </div>
      </div>
    </q-page>

    <position-filter
      v-if="$route.name.startsWith('position')"
      :show-filter-drawer="showFilterDrawer"
      @show-filter-drawer="
        (showFilter) => {
          showFilterDrawer = showFilter;
        }
      "
      @filter-active-change="
        (filtersActive) => {
          filtersActiveNo = filtersActive;
        }
      "
    ></position-filter>

    <movement-filter
      v-if="$route.name === 'movements'"
      :show-filter-drawer="showFilterDrawer"
      @show-filter-drawer="
        (showFilter) => {
          showFilterDrawer = showFilter;
        }
      "
      @filter-active-change="
        (filtersActive) => {
          filtersActiveNo = filtersActive;
        }
      "
    ></movement-filter>

    <inventory-filter
      v-if="$route.name === 'inventory'"
      v-model:show-filter-drawer="showFilterDrawer"
      @filter-active-change="
        (filtersActive) => {
          filtersActiveNo = filtersActive;
        }
      "
    ></inventory-filter>

    <counting-filter
      v-if="$route.name === 'counting'"
      v-model:show-filter-drawer="showFilterDrawer"
      @filter-active-change="
        (filtersActive) => {
          filtersActiveNo = filtersActive;
        }
      "
    ></counting-filter>
  </q-page-container>
</template>

<script>
import { Dialog, Notify } from 'quasar';
import { api } from '@/boot/axios';
import CountingFilter from '@/components/warehouse/counting/CountingFilter.vue';
import InventoryFilter from '@/components/warehouse/inventory/InventoryFilter.vue';
import MovementFilter from '@/components/warehouse/movement/MovementFilter.vue';
import PositionFilter from '@/components/warehouse/position/PositionFilter.vue';
import CountSessionScreen from '@/views/warehouse/counting/CountSessionScreen.vue';
import { XLSXDownload, XLSXGetData } from '@/lib/xlsxDownload';
import {
  useInventoryColumns,
  useMovementColumns,
  usePositionColumns,
} from 'app/src/composables/warehouse';

const warehouse_views = [
  { component: 'Inventory', route_name: 'inventory' },
  { component: 'Movements', route_name: 'movements' },
  { component: 'Lists', route_name: 'movementLists' },
  { component: 'Positions', route_name: 'positions' },
  { component: 'Counting', route_name: 'countSessions' },
];

const header_plus_footer_height = 80;

export default {
  name: 'WarehouseRoot',

  components: {
    CountingFilter,
    PositionFilter,
    MovementFilter,
    InventoryFilter,
  },

  setup() {
    const inventorColumns = useInventoryColumns();
    const positionColumns = usePositionColumns();
    const movementColumns = useMovementColumns();
    return { inventorColumns, positionColumns, movementColumns };
  },

  data() {
    return {
      // content_height: 0,
      show_movement_form: false,
      views: warehouse_views,
      showFilterDrawer: false,
      filtersActiveNo: 0,
      current_view: 0,
    };
  },

  methods: {
    updateHeight() {
      this.content_height =
        document.documentElement.clientHeight - header_plus_footer_height;
    },

    hasActiveFilters(params) {
      const filterKeys = [
        'product_search',
        'serial_search',
        'work_order_search',
        'list_search',
        'position_to',
        'position_from',
        'movement_type',
        'movement_status',
        'start_from',
        'start_to',
        'end_from',
        'end_to',
      ];
      return filterKeys.some((key) => !!params[key]);
    },

    hasActiveInventoryFilters(params) {
      const filterKeys = [
        'product_search',
        'serial_search',
        'position_search',
        'root_position_key',
      ];
      return filterKeys.some((key) => !!params[key]);
    },

    hasActivePositionFilters(params) {
      const filterKeys = [
        'search',
        'is_in_position',
        'contains_position',
        'created_min',
        'created_max',
      ];
      return filterKeys.some((key) => !!params[key]);
    },

    exportExcel() {
      switch (this.$route.name) {
        case 'inventory':
          this.exportInventory();
          break;
        case 'positions':
          this.exportPositions();
          break;
        case 'movements':
          this.exportMovements();
          break;
      }
    },

    async exportPositions() {
      const params = {
        ...this.$store.state.warehouse.position_search_params,
        limit: 50000,
        offset: 0,
      };

      const maxRecordsWarning = this.$t('warehouse.export_max_records_warning', { max: 50000 });

      if (!this.hasActivePositionFilters(params)) {
        Dialog.create({
          title: this.$t('warehouse.export_without_filters_title'),
          message: this.$t('warehouse.export_without_filters_message') + ' ' + maxRecordsWarning,
          cancel: true,
          persistent: true,
        }).onOk(() => {
          this.executeExportPositions(params);
        });
      } else {
        Dialog.create({
          title: this.$t('warehouse.export_limit_warning_title') || 'Export Limit',
          message: maxRecordsWarning,
          cancel: false,
          persistent: false,
        }).onOk(() => {
          this.executeExportPositions(params);
        });
      }
    },

    async executeExportPositions(params) {
      try {
        this.$q.loading.show();
        const { data } = await api.get('position', { params });
        XLSXDownload(
          XLSXGetData(data, this.positionColumns),
          'positions',
          'positions',
        );
      } catch (e) {
        console.error(e);
        Notify.create({
          message: 'Export failed',
          color: 'negative',
        });
      } finally {
        this.$q.loading.hide();
      }
    },

    async exportMovements() {
      const params = {
        ...this.$store.state.warehouse.movement_search_params,
        limit: 50000,
        offset: 0,
      };

      const maxRecordsWarning = this.$t('warehouse.export_max_records_warning', { max: 50000 });

      if (!this.hasActiveFilters(params)) {
        Dialog.create({
          title: this.$t('warehouse.export_without_filters_title'),
          message: this.$t('warehouse.export_without_filters_message') + ' ' + maxRecordsWarning,
          cancel: true,
          persistent: true,
        }).onOk(() => {
          this.executeExportMovements(params);
        });
      } else {
        Dialog.create({
          title: this.$t('warehouse.export_limit_warning_title') || 'Export Limit',
          message: maxRecordsWarning,
          cancel: false,
          persistent: false,
        }).onOk(() => {
          this.executeExportMovements(params);
        });
      }
    },

    async executeExportMovements(params) {
      try {
        this.$q.loading.show();
        const { data } = await api.get('movement', { params });
        XLSXDownload(
          XLSXGetData(data, this.movementColumns),
          'movements',
          'movements',
        );
      } catch (e) {
        console.error(e);
        Notify.create({
          message: 'Export failed',
          color: 'negative',
        });
      } finally {
        this.$q.loading.hide();
      }
    },

    async exportInventory() {
      const params = {
        ...this.$store.state.warehouse.inventory_search_params,
        limit: 50000,
        offset: 0,
      };

      if (!this.hasActiveInventoryFilters(params)) {
        Dialog.create({
          title: this.$t('warehouse.export_without_filters_title'),
          message: this.$t('warehouse.export_without_filters_message') + ' ' + this.$t('warehouse.export_max_records_warning', { max: 50000 }),
          cancel: true,
          persistent: true,
        }).onOk(() => {
          this.executeExportInventory(params);
        });
      } else {
        // Show warning about 50k limit even when filters are present
        Dialog.create({
          title: this.$t('warehouse.export_limit_warning_title') || 'Export Limit',
          message: this.$t('warehouse.export_max_records_warning', { max: 50000 }),
          cancel: false,
          persistent: false,
        }).onOk(() => {
          this.executeExportInventory(params);
        });
      }
    },

    async executeExportInventory(params) {
      try {
        this.$q.loading.show();
        const { data } = await api.get('inventory', { params });
        XLSXDownload(
          XLSXGetData(data, this.inventorColumns),
          'inventory',
          'inventory',
        );
      } catch (e) {
        console.error(e);
        Notify.create({
          message: 'Export failed',
          color: 'negative',
        });
      } finally {
        this.$q.loading.hide();
      }
    },
  },
};
</script>
