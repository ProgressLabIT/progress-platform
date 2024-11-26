<template>
  <FilterDrawer
    v-model="showFilterDrawer"
    :active-filters="filters_active"
    @reset="resetFilters"
  >
    <!-- SEARCH BOX -->
    <div class="row items-baseline q-col-gutter-md">
      <q-input
        v-model="search_string"
        filled
        dense
        clearable
        autocomplete="off"
        name="search"
        debounce="300"
        :label="$capitalize($t('search'))"
        class="q-mb-md col"
      >
        <template #append>
          <q-icon name="mdi-information-outline" class="col-auto" size="sm">
            <q-tooltip :delay="Number(300)" class="text-body2">
              <span>
                {{ $capitalize($t('production.search_explainer')) }}:
              </span>
              <ul>
                <li>{{ $capitalize($t('project')) }}</li>
              </ul>
            </q-tooltip>
          </q-icon>
        </template>
      </q-input>
    </div>

    <!-- IS IN POSITION -->
    <div class="row items-baseline q-col-gutter-md">
      <q-input
        v-model="is_in_position"
        filled
        dense
        clearable
        autocomplete="off"
        name="search"
        debounce="300"
        :label="$capitalize($t('is_in_position'))"
        class="q-mb-md col"
      >
        <template #append>
          <q-icon name="mdi-information-outline" class="col-auto" size="sm">
            <q-tooltip :delay="Number(300)" class="text-body2">
              <span>
                {{ $capitalize($t('production.search_explainer')) }}:
              </span>
              <ul>
                <li>{{ $capitalize($t('project')) }}</li>
              </ul>
            </q-tooltip>
          </q-icon>
        </template>
      </q-input>
    </div>

    <!-- CONTAINS POSITION -->
    <div class="row items-baseline q-col-gutter-md">
      <q-input
        v-model="contains_position"
        filled
        dense
        clearable
        autocomplete="off"
        name="search"
        debounce="300"
        :label="$capitalize($t('contains_position'))"
        class="q-mb-md col"
      >
        <template #append>
          <q-icon name="mdi-information-outline" class="col-auto" size="sm">
            <q-tooltip :delay="Number(300)" class="text-body2">
              <span>
                {{ $capitalize($t('production.search_explainer')) }}:
              </span>
              <ul>
                <li>{{ $capitalize($t('project')) }}</li>
              </ul>
            </q-tooltip>
          </q-icon>
        </template>
      </q-input>
    </div>

    <!-- DATE START RANGE -->
    <div class="row q-col-gutter-sm">
      <div class="col">
        <q-input
          v-model="created_min"
          filled
          dense
          clearable
          debounce="1000"
          mask="date"
          :label="
            $capitalize($t('work_order.list_headers.start_from')) +
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
                <q-date v-model="created_min" minimal>
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
          v-model="created_max"
          filled
          dense
          clearable
          mask="date"
          debounce="1000"
          :label="
            $capitalize($t('work_order.list_headers.start_from')) +
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
                <q-date v-model="created_max" minimal>
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
  name: 'PositionsFilter',

  components: {
    FilterDrawer,
  },

  data() {
    return {
      bool_filters: [],
      showFilterDrawer: false,
    };
  },

  computed: {
    // Filters
    search_string: queryModel(String, 'search', null),
    is_in_position: queryModel(String, 'is_in_position', null),
    contains_position: queryModel(String, 'contains_position', null),

    created_min: queryModel(String, 'created_min', null),
    created_max: queryModel(String, 'created_max', null),

    _this() {
      return this;
    },

    filters() {
      return {
        search_string: this.search_string,
        is_in_position: this.is_in_position,
        contains_position: this.contains_position,
        created_min: this.created_min,
        created_max: this.created_max,
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
