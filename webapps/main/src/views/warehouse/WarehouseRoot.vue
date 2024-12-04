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
          <template v-if="$route.name === 'positions'">
            <q-btn
              size="0.75rem"
              :label="$t('new')"
              color="theme-blue"
              @click="show_position_form = true"
            >
            </q-btn>
          </template>

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
      v-if="$route.name === 'positions'"
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
  </q-page-container>

  <PositionNewForm
    :show="show_position_form"
    mode="new"
    @close-position="show_position_form = false"
  >
  </PositionNewForm>
</template>

<script>
import MovementFilter from '@/components/warehouse/movement/MovementFilter.vue';
import PositionFilter from '@/components/warehouse/position/PositionFilter.vue';
import PositionNewForm from 'app/src/components/warehouse/position/PositionNewForm.vue';

const warehouse_views = [
  { component: 'Positions', route_name: 'positions' },
  { component: 'Stock', route_name: 'stock' },
  { component: 'Missions', route_name: 'missions' },
  { component: 'Movements', route_name: 'movements' },
];

const header_plus_footer_height = 80;

export default {
  name: 'WarehouseRoot',

  components: {
    PositionFilter,
    PositionNewForm,
    MovementFilter,
  },

  data() {
    return {
      // content_height: 0,
      show_position_form: false,
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
  },
};
</script>
