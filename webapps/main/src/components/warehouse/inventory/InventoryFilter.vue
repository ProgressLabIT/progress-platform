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
        :label="$capitalize($t('warehouse.inventory.product'))"
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
  </FilterDrawer>
</template>

<script>
import BaseAutocompletePositions from '@/components/BaseAutocompletePositions.vue';
import BaseAutocompleteProduct from '@/components/BaseAutocompleteProduct.vue';
import FilterDrawer from '@/components/FilterDrawer.vue';
import queryModel from '@/lib/queryModelFactory.js';

export default {
  name: 'InventoryFilter',

  components: {
    FilterDrawer,
    BaseAutocompletePositions,
    BaseAutocompleteProduct,
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

    _this() {
      return this;
    },

    filters() {
      return {
        produc: this.product,
        position: this.position,

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
