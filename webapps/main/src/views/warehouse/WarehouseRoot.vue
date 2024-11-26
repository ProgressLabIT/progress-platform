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
        </div>

        <!-- MAIN CONTENT -->
        <div class="col relative-position">
          <router-view />
        </div>
      </div>
    </q-page>

    <position-filter v-if="$route.name === 'positions'"></position-filter>
  </q-page-container>
</template>

<script>
import PositionFilter from 'app/src/components/warehouse/position/PositionFilter.vue';

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
  },

  data() {
    return {
      // content_height: 0,
      views: warehouse_views,
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
