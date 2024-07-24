<template>
  <q-page-container class="absolute-full">
    <q-page class="row full-height">
      <!-- MAIN CONTENT -->
      <div class="column col full-height">
        <div
          class="row col-auto items-center justify-between q-pl-xs q-pr-md q-py-sm"
        >
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

          <!-- NEW SERIAL BUTTON -->
          <q-btn
            size="0.75rem"
            :label="$t('new')"
            color="theme-blue"
            @click="show_serial_form = true"
          >
          </q-btn>

          <SerialForm
            :show="show_serial_form"
            mode="new"
            @close="show_serial_form = false"
            @serial-created="getSerials"
          >
          </SerialForm>

          <q-btn
            v-if="!showFilterDrawer && $route.name !== 'workOrderArchive'"
            class="q-ml-sm"
            size="sm"
            round
            :color="filters_active ? 'theme-blue' : 'theme-grey'"
            icon="mdi-filter"
            @click="showFilterDrawer = true"
          >
            <q-badge
              v-if="filters_active"
              floating
              rounded
              color="theme-red"
              :label="filters_active"
              size="4px"
              style="font-family: 'Red Hat Text'; font-size: 8px"
            />
          </q-btn>
        </div>

        <!-- MAIN CONTENT-->
        <div class="col relative-position">
          <router-view
            :loading="loading || loading_fields"
            @on-scroll="addSerials"
          />
        </div>
      </div>
    </q-page>

    <FilterDrawer
      v-model="showFilterDrawer"
      :active-filters="filters_active"
      @reset="resetFilters"
    >
      <!-- SERIAL KEY -->
      <!--   <q-input
        v-model="serial_key_search"
        clearable
        filled
        dense
        hide-bottom-space
        autocomplete="off"
        name="search"
        debounce="1000"
        :label="$t('serial_key')"
        class="q-mb-md"
      >
        <template #append>
          <q-icon name="mdi-magnify" />
        </template>
      </q-input>
 -->
      <!-- SERIAL NO -->
      <q-input
        v-model="serial_search"
        clearable
        filled
        dense
        hide-bottom-space
        autocomplete="off"
        name="search"
        debounce="1000"
        :label="$t('serial')"
        class="q-mb-md"
      >
        <template #append>
          <q-icon name="mdi-magnify" />
        </template>
      </q-input>

      <q-input
        v-model="is_contained_in"
        clearable
        filled
        dense
        hide-bottom-space
        autocomplete="off"
        name="search"
        debounce="1000"
        :label="$t('serial.is_contained_in')"
        class="q-mb-md"
      >
        <template #append>
          <q-icon name="mdi-magnify" />
        </template>
      </q-input>

      <q-input
        v-model="contains"
        clearable
        filled
        dense
        hide-bottom-space
        autocomplete="off"
        name="search"
        debounce="1000"
        :label="$t('serial.contains')"
        class="q-mb-md"
      >
        <template #append>
          <q-icon name="mdi-magnify" />
        </template>
      </q-input>

      <!-- PRODUCT -->
      <q-input
        v-model="product_code_search"
        clearable
        dense
        filled
        hide-bottom-space
        autocomplete="off"
        name="product"
        debounce="1000"
        class="q-mb-md"
        :label="$t('product.label')"
      >
        <template #append>
          <q-icon name="mdi-magnify" />
        </template>
      </q-input>

      <!-- WORK ORDER -->
      <q-input
        v-model="work_order_search"
        clearable
        dense
        filled
        hide-bottom-space
        autocomplete="off"
        name="product"
        debounce="1000"
        class="q-mb-md"
        :label="$t('work_order.long')"
      >
        <template #append>
          <q-icon name="mdi-magnify" />
        </template>
      </q-input>

      <!-- OPENED DATE RANGE -->
      <div class="row q-col-gutter-sm q-mb-md">
        <div class="col">
          <q-input
            v-model="time_created_from"
            filled
            dense
            clearable
            debounce="1000"
            mask="date"
            :label="$t('created_min')"
          >
            <template #append>
              <q-icon name="mdi-calendar" size="xs" class="cursor-pointer">
                <q-popup-proxy
                  cover
                  transition-show="scale"
                  transition-hide="scale"
                >
                  <q-date v-model="time_created_from" minimal>
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
            v-model="time_created_to"
            filled
            dense
            clearable
            mask="date"
            debounce="1000"
            :label="$t('created_max')"
          >
            <template #append>
              <q-icon name="mdi-calendar" size="xs" class="cursor-pointer">
                <q-popup-proxy
                  cover
                  transition-show="scale"
                  transition-hide="scale"
                >
                  <q-date v-model="time_created_to" minimal>
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

      <!-- OPENED BY -->
      <BaseAutocompleteUser
        :placeholder="$capitalize($t('opened_by'))"
        dense
        class="q-mb-md"
        behavior="menu"
        key-only
        :label="$t('opened_by')"
        :operator-only="false"
        :value="created_by"
        @select="(selection) => (created_by = selection)"
      />

      <!--
      <div class="col-6">
        <q-checkbox
          v-model="serial_deleted"
          dense
          :label="$t('traceability.include_deleted')"
        />
      </div>-->

      <div
        v-for="filter in serial_fields"
        :key="filter._key"
        class="row items-center justify-between q-mt-sm"
      >
        <div class="col">
          <q-checkbox
            v-if="filter.type === 'files'"
            v-model="filter.value"
            :label="$t('has_attachments')"
          />

          <FormField
            v-else
            :field="filter"
            style="margin-bottom: 0"
            dense
            @update="
              filter.value = filter.type === 'choice' ? $event?.value : $event
            "
          />
        </div>
      </div>

      <div class="row items-center justify-between">
        <div class="highlight text-uppercase text-h6">
          {{ $t('advanced_filters') }}
        </div>

        <q-space />

        <q-btn-toggle
          v-model="advancedFilterOperator"
          :options="[
            { label: $t('all', 2), value: 'AND' },
            { label: $t('any'), value: 'OR' },
          ]"
          size="xs"
          class="q-mr-md"
        />

        <q-btn
          round
          color="theme-blue"
          icon="mdi-plus"
          size="xs"
          @click="addAdvancedFilter"
        />
      </div>

      <div
        v-for="(filter, index) in advancedFilters"
        :key="filter._key"
        class="row items-center justify-between q-mt-sm"
      >
        <div class="col">
          <q-checkbox
            v-if="filter.type === 'files'"
            v-model="filter.value"
            :label="$t('has_attachments')"
          />
          <!-- We override q-mb-lg of FormField with style -->
          <FormField
            v-else
            :field="filter"
            style="margin-bottom: 0"
            dense
            @update="
              filter.value = filter.type === 'choice' ? $event?.value : $event
            "
          />
        </div>

        <q-btn
          class="q-ml-md"
          round
          color="theme-grey"
          icon="mdi-minus"
          size="xs"
          @click="advancedFilters.splice(index, 1)"
        />
      </div>
    </FilterDrawer>
  </q-page-container>
</template>

<script>
import { Dialog, uid } from 'quasar';
import { ref, watch } from 'vue';
import { useStore } from 'vuex';
import AddAdvancedFilterDialog from '@/components/AddAdvancedFilterDialog.vue';
import BaseAutocompleteUser from '@/components/BaseAutocompleteUser.vue';
import FilterDrawer from '@/components/FilterDrawer.vue';
import FormField from '@/components/FormField.vue';
import queryModel, { useQueryModel } from '@/lib/queryModelFactory.js';
import SerialForm from 'app/src/components/traceability/SerialForm.vue';

export default {
  name: 'TraceabilityRoot',

  components: {
    BaseAutocompleteUser,
    SerialForm,
    FormField,
    FilterDrawer,
  },

  setup() {
    const store = useStore();

    const showFilterDrawer = ref(false);
    const advancedFilterOperator = ref('AND');
    // Contains local form fields referencing to actual custom fields
    const advancedFilters = ref([]);

    function addAdvancedFilter() {
      Dialog.create({
        component: AddAdvancedFilterDialog,
      }).onOk((formField) => {
        advancedFilters.value.push(formField);
      });
    }

    const advancedFilterQuery = useQueryModel(Object, 'advanced_filters', null);
    watch(
      [advancedFilters, advancedFilterOperator],
      ([advancedFilters, operator]) => {
        if (advancedFilters.length === 0) {
          advancedFilterQuery.value = null;
          return;
        }

        advancedFilterQuery.value = {
          operator,
          filters: advancedFilters.map(({ custom_field_key, value }) => ({
            _key: custom_field_key,
            value,
          })),
        };
      },
      { deep: true },
    );

    const initialQuery = advancedFilterQuery.value;
    if (initialQuery) {
      (async () => {
        advancedFilterOperator.value = initialQuery.operator;
        advancedFilters.value = initialQuery.filters.map(({ _key, value }) => {
          const customField = store.getters.getCustomFieldByKey(_key);
          return {
            _key: uid(), // local-only
            custom_field_key: _key,
            label: customField.default_label,
            hint: customField.default_hint,
            value,
          };
        });
      })();
    }

    return {
      showFilterDrawer,
      advancedFilterOperator,
      advancedFilters,
      addAdvancedFilter,
      advancedFilterQuery,
    };
  },

  data() {
    return {
      views: [{ component: 'SerialOverview', route_name: 'serialOverview' }],
      filter_list: [
        'serial_key_search',
        'work_order_search',
        'serial_search',
        'is_contained_in',
        'contains',
        'created_by',
        'time_created_from',
        'time_created_to',
        'product_code_search',
        //'serial_deleted',
      ],
      bool_filters: [
        /*'serial_deleted'*/
      ],
      loading: false,
      loading_fields: false,
      show_serial_form: false,
      events: NaN,
      serial_fields: [],
      limit: 200,
      offset: 0,
    };
  },

  computed: {
    filters_active() {
      return (
        this.advancedFilters.length +
        this.filter_list.filter((f) => {
          return this.bool_filters.includes(f) ? this[f] === false : !!this[f];
        }).length
      );
    },

    serial_key_search: queryModel(String, 'serial_search', null),
    serial_search: queryModel(String, 'serial', null),
    is_contained_in: queryModel(String, 'is_contained_in', null),
    contains: queryModel(String, 'contains', null),
    product_code_search: queryModel(String, 'product_code_search', null),
    work_order_search: queryModel(String, 'work_order_search', null),
    created_by: queryModel(String, 'opened_by', null),
    time_created_from: queryModel(String, 'opened_min', null),
    time_created_to: queryModel(String, 'opened_max', null),
    //serial_deleted: queryModel(Boolean, 'deleted', false),

    max_shown() {
      return this.load_quantity * this.loading_round;
    },

    filters() {
      let filters_object = {};
      this.filter_list.forEach((f) => {
        if (this[f] != undefined) {
          if (f.startsWith('time')) {
            const date = new Date(this[f]);

            // The api handles full timestamps, thus to include serials created/closed during the day indicated we need to set the filter at the end of the same
            if (f.endsWith('_to')) {
              // Not using UTC time on purpose, to correctly represent the filter wanted by the user
              date.setHours(23, 59, 59, 999);
            }

            filters_object[f] = date.toISOString();
          } else if (this.bool_filters.includes(f)) {
            if (this[f] == false) {
              filters_object[f] = this[f];
            }
          } else {
            filters_object[f] = this[f];
          }
        }
      });
      return {
        ...filters_object,
        limit: this.limit,
        advanced_filters: this.advancedFilterQuery
          ? btoa(JSON.stringify(this.advancedFilterQuery))
          : null,
      };
    },
  },

  watch: {
    filters: {
      deep: true,
      handler: 'getSerials',
    },
  },

  created() {
    this.getSerialFields();
    this.getSerials();
    let eventURL =
      this.$api.defaults.baseURL + '/notification/serial-notification';
    this.events = new EventSource(eventURL, {
      withCredentials: false,
    });
    this.events.addEventListener('serial-notification', (event) => {
      this.handleMessage(event);
    });
  },

  beforeUnmount() {
    if (this.events) {
      this.events.close();
    }
  },

  methods: {
    getErrorMessage(error_code, default_message) {
      let message = this.$t('traceability.errors.' + error_code);
      if (message) {
        return message;
      }
      return this.$t(default_message);
    },

    handleMessage(message) {
      this.refreshSerial();
      let event = JSON.parse(message.data);
      if (event.notification === 'ERROR') {
        this.$q.notify({
          message: this.getErrorMessage(event.error_code, event.error),
          color: 'theme-red',
          timeout: 1500,
          position: 'top',
        });
      }
    },

    refreshSerial() {
      this.$store.dispatch('getSerials', { serial_key: this.serialKey });
    },

    async resetFilters() {
      await this.$router.replace({ query: null });
      this.advancedFilters = [];
    },

    async getSerialFields() {
      this.loading_fields = true;

      await this.$store.dispatch('getSerialFields', {}).then(() =>
        setTimeout(() => {
          this.loading_fields = false;
        }, 1000),
      );

      //this.serial_fields = this.$store.state.serial.serial_fields;
      this.serial_fields = [];
    },

    getSerials() {
      this.loading = true;
      this.offset = 0;
      this.$store
        .dispatch('getSerials', {
          ...this.filters,
          offset: this.offset,
        })
        .then(() =>
          setTimeout(() => {
            this.loading = false;
          }, 1000),
        );
    },

    hasMore() {
      return this.limit + this.offset <= this.$store.getters.getSerialCount();
    },

    addSerials(data) {
      const lastIndex = this.$store.getters.getSerialCount() - 1;

      if (this.loading !== true && data.to === lastIndex && this.hasMore()) {
        this.offset += this.limit;
        this.loading = true;
        this.$store
          .dispatch('appendSerials', {
            ...this.filters,
            offset: this.offset,
          })
          .then(() =>
            setTimeout(() => {
              this.loading = false;
            }, 1000),
          );
      }
    },
  },
};
</script>

<style lang="sass" scoped>
.fade-bottom-bg
  position: relative

.fade-bottom-bg::after
  content: "" // ::before and ::after both require content
  position: absolute
  bottom: 0
  left: 0
  right: 0
  height: 80px
  background-image: linear-gradient(to top, var(--bg-color) 0%, transparent)
  // background-color: linear-gradient(to top, var(--bg-color), transparent 10%)
  // background-image: linear-gradient(120deg, #eaee44, #33d0ff);
</style>
