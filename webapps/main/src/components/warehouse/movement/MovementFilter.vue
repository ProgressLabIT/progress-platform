<template>
  <FilterDrawer
    v-model="showFilter"
    :active-filters="filters_active"
    @reset="resetFilters"
  >
    <!-- PRODUCT CODE -->
    <q-input
      v-model="product_code"
      filled
      dense
      clearable
      autocomplete="off"
      name="search"
      debounce="300"
      :label="$capitalize($t('product.code'))"
      class="q-mb-md col"
    />


    <!-- MOVEMENT TYPE -->
    <q-select
      v-model="movement_type"
      :options="movement_type_options"
      use-input
      filled
      dense
      clearable
      input-debounce="100"
      class="q-mb-md col"
      :label="$capitalize($t('warehouse.movement.movement_type'))"
    />

    <!-- STATUS -->
    <q-select
      v-model="movement_status"
      :options="status_options"
      use-input
      filled
      dense
      clearable
      input-debounce="100"
      class="q-mb-md col"
      :label="$capitalize($t('warehouse.movement.status'))"
    />

    <!-- DATE FILTERS -->
    <div class="row q-col-gutter-sm">
      <div class="col-6">
        <q-input
          v-model="start_from"
          filled
          dense
          clearable
          debounce="1000"
          mask="date"
          :label="
            $capitalize($t('warehouse.movement.start_from')) +
            ' (' +
            $t('min') +
            ')'
          "
        >
          <template #append>
            <q-icon name="mdi-calendar" size="xs" class="cursor-pointer">
              <q-popup-proxy
                cover
                transition-show="scale"
                transition-hide="scale"
              >
                <q-date v-model="start_from" minimal>
                  <div class="row items-center justify-end">
                    <q-btn v-close-popup label="Close" color="primary" flat />
                  </div>
                </q-date>
              </q-popup-proxy>
            </q-icon>
          </template>
        </q-input>
      </div>
      <div class="col-6">
        <q-input
          v-model="start_to"
          filled
          dense
          clearable
          mask="date"
          debounce="1000"
          :label="
            $capitalize($t('warehouse.movement.start_to')) +
            ' (' +
            $t('max') +
            ')'
          "
        >
          <template #append>
            <q-icon name="mdi-calendar" size="xs" class="cursor-pointer">
              <q-popup-proxy
                cover
                transition-show="scale"
                transition-hide="scale"
              >
                <q-date v-model="start_to" minimal>
                  <div class="row items-center justify-end">
                    <q-btn v-close-popup label="Close" color="primary" flat />
                  </div>
                </q-date>
              </q-popup-proxy>
            </q-icon>
          </template>
        </q-input>
      </div>
      <div class="col-6">
        <q-input
          v-model="end_from"
          filled
          dense
          clearable
          debounce="1000"
          mask="date"
          :label="
            $capitalize($t('warehouse.movement.end_from')) +
            ' (' +
            $t('min') +
            ')'
          "
        >
          <template #append>
            <q-icon name="mdi-calendar" size="xs" class="cursor-pointer">
              <q-popup-proxy
                cover
                transition-show="scale"
                transition-hide="scale"
              >
                <q-date v-model="end_from" minimal>
                  <div class="row items-center justify-end">
                    <q-btn v-close-popup label="Close" color="primary" flat />
                  </div>
                </q-date>
              </q-popup-proxy>
            </q-icon>
          </template>
        </q-input>
      </div>
      <div class="col-6">
        <q-input
          v-model="end_to"
          filled
          dense
          clearable
          mask="date"
          debounce="1000"
          :label="
            $capitalize($t('warehouse.movement.end_to')) +
            ' (' +
            $t('max') +
            ')'
          "
        >
          <template #append>
            <q-icon name="mdi-calendar" size="xs" class="cursor-pointer">
              <q-popup-proxy
                cover
                transition-show="scale"
                transition-hide="scale"
              >
                <q-date v-model="end_to" minimal>
                  <div class="row items-center justify-end">
                    <q-btn v-close-popup label="Close" color="primary" flat />
                  </div>
                </q-date>
              </q-popup-proxy>
            </q-icon>
          </template>
        </q-input>
      </div>
    </div>

     <!-- POSITION FILTERS -->
    <div class="row items-baseline q-gutter-md q-mt-md q-mb-md">
      <div class="weight-bold text-low text-uppercase text-h6">
        {{ $t('warehouse.movement.position_filters') }}
      </div>

      <q-space />

      <q-btn-toggle
        v-model="positionFilterOperator"
        :options="[
          { label: $t('all', 2), value: 'AND' },
          { label: $t('any'), value: 'OR' },
        ]"
        size="xs"
      />
    </div>

    <div class="row items-baseline q-col-gutter-md">
      <BaseAutocompletePositions
        dense
        filled
        class="q-mb-md col"
        behavior="menu"
        popup-content-class="z-max"
        key-only
        :load-data="false"
        :label="$capitalize($t('warehouse.movement.position_from_code'))"
        :value="position_from"
        @select="(selection) => (position_from = selection)"
      />
    </div>

    <div class="row items-baseline q-col-gutter-md">
      <BaseAutocompletePositions
        dense
        filled
        class="q-mb-md col"
        behavior="menu"
        popup-content-class="z-max"
        key-only
        :load-data="false"
        :label="$capitalize($t('warehouse.movement.position_to_code'))"
        :value="position_to"
        @select="(selection) => (position_to = selection)"
      />
    </div>

    <!-- POSITION HIERARCHY -->
    <q-checkbox
      v-model="search_graph"
      label="Includi posizioni interne"
    />

    <!-- REFERENCES -->
    <div class="weight-bold text-low text-uppercase text-h6 q-mt-md q-mb-md">
      Riferimenti
    </div>

    <!-- WORK ORDER -->
    <q-input
      v-model="work_order"
      filled
      dense
      clearable
      class="q-mb-md"
      label="Ordine di produzione"
    />

    <!-- LIST FILTER -->
    <q-input
      v-model="list"
      filled
      dense
      clearable
      label="Lista movimenti"
    />

  </FilterDrawer>
</template>

<script>
import BaseAutocompletePositions from '@/components/BaseAutocompletePositions.vue';
import FilterDrawer from '@/components/FilterDrawer.vue';
import queryModel from '@/lib/queryModelFactory.js';

export default {
  name: 'MovementFilter',

  components: {
    FilterDrawer,
    BaseAutocompletePositions,
  },

  props: {
    showFilterDrawer: {
      type: Boolean,
      required: true,
    },
  },

  emits: ['showFilterDrawer', 'filterActiveChange'],

  data() {
    return {
      bool_filters: ['search_graph'],
      movement_type_options: [
        'transfer',
        'receipt',
        'shipment',
        'production',
        'consumption',
        'adjustment',
      ],
      status_options: ['planned', 'started', 'completed', 'canceled'],
      showFilter: false,
    };
  },

  computed: {
    // Filters
    product_search: queryModel(String, 'product_search', null),
    serial_search: queryModel(String, 'serial_search', null),
    work_order: queryModel(String, 'work_order_search', null),
    list: queryModel(String, 'list_search', null),
    search_graph: queryModel(Boolean, 'search_graph', true),

    position_to: queryModel(String, 'position_to', null),
    position_from: queryModel(String, 'position_from', null),

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

    _this() {
      return this;
    },

    filters() {
      return {
        product_search: this.product_code,
        serial_code_search: this.serial_code,
        work_order_code_search: this.work_order_code,
        list_code_search: this.list_code,

        position_from: this.position_from,
        position_to: this.position_to,
        // search_graph is not a filter, it's a parameter
        // position_filter_operator is not a filter, it's a parameter

        movement_type: this.movement_type,
        movement_status: this.movement_status,

        start_from: this.start_from,
        start_to: this.start_to,
        end_from: this.end_from,
        end_to: this.end_to,

        work_order: this.work_order,
        list: this.list,
      };
    },

    filters_active() {
      return Object.entries(this.filters).filter(([name, value]) => {
        return [...this.bool_filters].includes(name)
          ? value === false
          : !!value;
      }).length;
    },
  },

  watch: {
    showFilter: {
      handler() {
        this.$emit('showFilterDrawer', this.showFilter);
      },
    },
    showFilterDrawer: {
      handler() {
        this.showFilter = this.showFilterDrawer;
        this.$emit('filterActiveChange', this.filters_active);
      },
    },
  },

  methods: {
    setSearch(text) {
      this.search_string = text;
    },

    resetFilters() {
      this.$router.replace({ query: null });
    },
  },
};
</script>
