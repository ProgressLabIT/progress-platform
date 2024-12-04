<template>
  <FilterDrawer
    v-model="showFilter"
    :active-filters="filters_active"
    @reset="resetFilters"
  >
    <!-- PRODUCT CODE -->
    <div class="row items-baseline q-col-gutter-md">
      <q-input
        v-model="product_code"
        filled
        dense
        clearable
        autocomplete="off"
        name="search"
        debounce="300"
        :label="$capitalize($t('warehouse.movement.product_code'))"
        class="q-mb-md col"
      >
      </q-input>
    </div>

    <!-- THROUGH POSITION -->
    <div class="row items-baseline q-col-gutter-md">
      <q-input
        v-model="through_position_code"
        filled
        dense
        clearable
        autocomplete="off"
        name="search"
        debounce="300"
        :label="$capitalize($t('warehouse.movement.through_position_code'))"
        class="q-mb-md col"
      >
      </q-input>
    </div>

    <!-- Movement Type -->
    <div class="row items-baseline q-col-gutter-md">
      <q-select
        v-model="movement_type"
        :options="movement_type_options"
        use-input
        filled
        input-debounce="100"
        class="q-mb-md col"
        :label="$capitalize($t('warehouse.movement.movement_type'))"
      />
    </div>

    <!-- Status -->
    <div class="row items-baseline q-col-gutter-md">
      <q-select
        v-model="movement_status"
        :options="status_options"
        use-input
        filled
        input-debounce="100"
        class="q-mb-md col"
        :label="$capitalize($t('warehouse.movement.status'))"
      />
    </div>

    <!-- DATE START RANGE -->
    <div class="row q-col-gutter-sm">
      <div class="col">
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
      <div class="col">
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
    </div>

    <!-- DATE END RANGE -->
    <div class="row q-col-gutter-sm">
      <div class="col">
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
      <div class="col">
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
  </FilterDrawer>
</template>

<script>
import FilterDrawer from '@/components/FilterDrawer.vue';
import queryModel from '@/lib/queryModelFactory.js';

export default {
  name: 'MovementFilter',

  components: {
    FilterDrawer,
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
      bool_filters: [],
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
    product_code: queryModel(String, 'product_code', null),
    through_position_code: queryModel(String, 'through_position_code', null),

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
        produc_code: this.produc_code,
        through_position_code: this.through_position_code,

        movement_type: this.movement_type,
        movement_status: this.movement_status,

        start_from: this.start_from,
        start_to: this.start_to,
        end_from: this.end_from,
        end_to: this.end_to,
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
