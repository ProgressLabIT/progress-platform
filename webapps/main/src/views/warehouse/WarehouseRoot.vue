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
import { Dialog } from 'quasar';
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

    exportPositions() {
      XLSXDownload(
        XLSXGetData(
          this.$store.state.warehouse.positions,
          this.positionColumns,
        ),
        'positions',
        'positions',
      );
    },

    exportMovements() {
      XLSXDownload(
        XLSXGetData(
          this.$store.state.warehouse.movements,
          this.movementColumns,
        ),
        'movements',
        'movements',
      );
    },

    exportInventory() {
      XLSXDownload(
        XLSXGetData(
          this.$store.state.warehouse.inventory,
          this.inventorColumns,
        ),
        'inventory',
        'inventory',
      );
      /* XLSXDownload(
        this.$store.state.warehouse.inventory.map((entry) => {
          return {
            [this.$t('warehouse.inventory.position').toUpperCase()]:
              entry.position_code,
            [this.$t('warehouse.inventory.product_code').toUpperCase()]:
              entry.product_code,
            [this.$t('warehouse.inventory.serial').toUpperCase()]:
              entry.serial_code,
            [this.$t('warehouse.inventory.quantity').toUpperCase()]:
              entry.quantity,
            [this.$t('warehouse.inventory.owned').toUpperCase()]: entry.owned,
            [this.$t('warehouse.inventory.date_received').toUpperCase()]:
              this.$shortDateString(entry.date_received, this.$i18n.locale),
            [this.$t('warehouse.inventory.expiration_date').toUpperCase()]:
              this.$shortDateString(entry.expiration_date, this.$i18n.locale),
          };
          let row = {};
          this.inventorColumns.map((col) => {
            row[col.label] = entry[col.field];
          });
          return row;
        }),
        'inventory',
        'inventory',
      );*/
    },
  },
};
</script>
