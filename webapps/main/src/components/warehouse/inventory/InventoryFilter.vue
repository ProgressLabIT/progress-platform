<template>
  <FilterDrawer
    v-model="showFilter"
    :active-filters="filters_active"
    @reset="resetFilters"
  >
    <!-- PRODUCT CODE -->
    <div class="row items-baseline q-col-gutter-md">
      <BaseAutocompleteProduct
        dense
        filled
        class="q-mb-md col"
        behavior="menu"
        popup-content-class="z-max"
        key-only
        :load-data="false"
        :label="$capitalize($t('warehouse.inventory.product_code'))"
        :value="product"
        @select="(selection) => (product = selection)"
      />
    </div>

    <!-- POSITION -->
    <div class="row items-baseline q-col-gutter-md">
      <BaseAutocompletePositions
        dense
        filled
        class="q-mb-md col"
        behavior="menu"
        popup-content-class="z-max"
        key-only
        :load-data="false"
        :label="$capitalize($t('warehouse.inventory.position'))"
        :value="position"
        @select="(selection) => (position = selection)"
      />
    </div>

    <!-- SERIAL -->
    <div class="row items-baseline q-col-gutter-md">
      <BaseAutocompleteSerial
        dense
        filled
        class="q-mb-md col"
        behavior="menu"
        popup-content-class="z-max"
        key-only
        :load-data="false"
        :label="$capitalize($t('serial'))"
        :value="serial"
        @select="(selection) => (serial = selection)"
      />
    </div>
  </FilterDrawer>
</template>

<script>
import BaseAutocompletePositions from '@/components/BaseAutocompletePositions.vue';
import BaseAutocompleteProduct from '@/components/BaseAutocompleteProduct.vue';
import BaseAutocompleteSerial from '@/components/BaseAutocompleteSerial.vue';
import FilterDrawer from '@/components/FilterDrawer.vue';
import queryModel from '@/lib/queryModelFactory.js';

export default {
  name: 'InventoryFilter',

  components: {
    FilterDrawer,
    BaseAutocompletePositions,
    BaseAutocompleteProduct,
    BaseAutocompleteSerial,
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
      showFilter: false,
    };
  },

  computed: {
    // Filters
    product: queryModel(String, 'product', null),
    position: queryModel(String, 'position', null),
    serial: queryModel(String, 'serial', null),

    _this() {
      return this;
    },

    filters() {
      return {
        product_key: this.product,
        position_key: this.position,
        serial_keys: this.serial,
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
    resetFilters() {
      this.$router.replace({ query: null });
    },
  },
};
</script>
