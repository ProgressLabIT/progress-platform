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

          <!-- NEW ISSUE BUTTON -->
          <q-btn
            size="0.75rem"
            :label="$t('new')"
            color="theme-blue"
            @click="show_issue_form = true"
          >
          </q-btn>

          <IssueForm
            :show="show_issue_form"
            mode="new"
            with_links
            @close="show_issue_form = false"
            @issue-created="getIssues"
          >
          </IssueForm>

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

        <!-- MAIN CONTENT -->
        <div class="col relative-position">
          <router-view :loading="loading" />
        </div>
      </div>
    </q-page>

    <FilterDrawer
      v-model="showFilterDrawer"
      :active-filters="filters_active"
      @reset="resetFilters"
    >
      <div class="row q-col-gutter-md q-mb-md">
        <div class="col-6">
          <q-checkbox v-model="issue_open" dense :label="$t('issue_open')" />
        </div>

        <div class="col-6">
          <q-checkbox
            v-model="issue_closed"
            dense
            :label="$t('issue_closed')"
          />
        </div>

        <div class="col-6">
          <q-checkbox
            v-model="issue_critical"
            dense
            :label="$t('issue_critical')"
          />
        </div>

        <div class="col-6">
          <q-checkbox
            v-model="issue_non_critical"
            dense
            :label="$t('issue_non_critical')"
          />
        </div>
      </div>

      <!-- ISSUE KEY -->
      <q-input
        v-model="issue_key_search"
        clearable
        filled
        dense
        hide-bottom-space
        autocomplete="off"
        name="search"
        debounce="1000"
        :label="$t('issue_key')"
        class="q-mb-md"
      >
        <template #append>
          <q-icon name="mdi-magnify" />
        </template>
      </q-input>

      <!-- ISSUE TYPE -->
      <BaseAutocompleteIssueType
        dense
        key-only
        class="q-mb-md"
        behavior="menu"
        :value="issue_type_key"
        @select="(selection) => (issue_type_key = selection)"
      />

      <!-- OPENED DATE RANGE -->
      <div class="row q-col-gutter-sm">
        <div class="col">
          <q-input
            v-model="time_created_from"
            filled
            dense
            clearable
            debounce="1000"
            mask="date"
            :label="$t('opened_min')"
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
            :label="$t('opened_max')"
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

      <!-- CLOSED DATE RANGE -->
      <div class="row q-col-gutter-sm q-mt-sm q-mb-md">
        <div class="col">
          <q-input
            v-model="time_closed_from"
            filled
            dense
            clearable
            mask="date"
            debounce="1000"
            :label="$t('closed_min')"
          >
            <template #append>
              <q-icon name="mdi-calendar" size="xs" class="cursor-pointer">
                <q-popup-proxy
                  cover
                  transition-show="scale"
                  transition-hide="scale"
                >
                  <q-date v-model="time_closed_from" minimal>
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
            v-model="time_closed_to"
            filled
            dense
            clearable
            mask="date"
            debounce="1000"
            :label="$t('closed_max')"
          >
            <template #append>
              <q-icon name="mdi-calendar" size="xs" class="cursor-pointer">
                <q-popup-proxy
                  cover
                  transition-show="scale"
                  transition-hide="scale"
                >
                  <q-date v-model="time_closed_to" minimal>
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

      <!-- CLOSED BY -->
      <BaseAutocompleteUser
        :placeholder="$capitalize($t('closed_by'))"
        dense
        class="q-mb-md"
        behavior="menu"
        key-only
        :label="$t('closed_by')"
        :operator-only="false"
        :value="closed_by"
        @select="(selection) => (closed_by = selection)"
      />

      <!-- OPERATION -->
      <BaseAutocompleteOperation
        dense
        filled
        class="q-mb-md"
        behavior="menu"
        popup-content-class="z-max"
        key-only
        :label="$capitalize($t('operation.label'))"
        :value="operation_key"
        @select="(selection) => (operation_key = selection)"
      />

      <!-- PRODUCT -->
      <q-input
        v-model="product_code_search"
        clearable
        dense
        filled
        hide-bottom-space
        autocomplete="off"
        name="work_order"
        debounce="1000"
        class="q-mb-md"
        :label="$t('product.label')"
      >
        <template #append>
          <q-icon name="mdi-magnify" />
        </template>
      </q-input>

      <!-- PHASE -->
      <q-input
        v-model="phase_alias_search"
        clearable
        dense
        filled
        hide-bottom-space
        autocomplete="off"
        name="work_order"
        debounce="1000"
        :label="$t('phase.short')"
        class="q-mb-md"
      >
        <template #append>
          <q-icon name="mdi-magnify" />
        </template>
      </q-input>

      <!-- WORK ORDER -->
      <q-input
        v-model="work_order_code_search"
        clearable
        filled
        dense
        hide-bottom-space
        autocomplete="off"
        name="work_order"
        debounce="1000"
        :label="$capitalize($t('work_order.long'))"
        class="q-mb-md"
      >
        <template #append>
          <q-icon name="mdi-magnify" />
        </template>
      </q-input>

      <!-- PROJECT -->
      <q-input
        v-model="project_search"
        clearable
        filled
        dense
        hide-bottom-space
        autocomplete="off"
        name="work_order"
        debounce="1000"
        :label="$capitalize($t('project'))"
        class="q-mb-md"
      >
        <template #append>
          <q-icon name="mdi-magnify" />
        </template>
      </q-input>

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
import BaseAutocompleteIssueType from '@/components/BaseAutocompleteIssueType.vue';
import BaseAutocompleteOperation from '@/components/BaseAutocompleteOperation.vue';
import BaseAutocompleteUser from '@/components/BaseAutocompleteUser.vue';
import FilterDrawer from '@/components/FilterDrawer.vue';
import FormField from '@/components/FormField.vue';
import IssueForm from '@/components/IssueForm.vue';
import queryModel, { useQueryModel } from '@/lib/queryModelFactory.js';

export default {
  name: 'TraceabilityRoot',

  components: {
    BaseAutocompleteIssueType,
    BaseAutocompleteOperation,
    BaseAutocompleteUser,
    IssueForm,
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
      views: [{ component: 'IssueOverview', route_name: 'issueOverview' }],
      filter_list: [
        'issue_key_search',
        'created_by',
        'time_created_from',
        'time_created_to',
        'closed_by',
        'time_closed_from',
        'time_closed_to',
        'issue_type_key',
        'operation_key',
        'work_order_code_search',
        'product_code_search',
        'phase_alias_search',
        'project_search',
        'issue_critical',
        'issue_non_critical',
        'issue_open',
        'issue_closed',
      ],
      bool_filters: [
        'issue_open',
        'issue_closed',
        'issue_critical',
        'issue_non_critical',
      ],
      loading: false,
      show_issue_form: false,
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

    issue_key_search: queryModel(String, 'issue_search', null),
    issue_type_key: queryModel(String, 'issue_type', null),
    issue_open: queryModel(Boolean, 'open', true),
    issue_closed: queryModel(Boolean, 'closed', true),
    issue_critical: queryModel(Boolean, 'critical', true),
    issue_non_critical: queryModel(Boolean, 'non_critical', true),
    operation_key: queryModel(String, 'operation', null),
    product_code_search: queryModel(String, 'product_search', null),
    work_order_code_search: queryModel(String, 'work_order_search', null),
    phase_alias_search: queryModel(String, 'phase_search', null),
    project_search: queryModel(String, 'project_search', null),
    created_by: queryModel(String, 'opened_by', null),
    time_created_from: queryModel(String, 'opened_min', null),
    time_created_to: queryModel(String, 'opened_max', null),
    closed_by: queryModel(String, 'closed_by', null),
    time_closed_from: queryModel(String, 'closed_min', null),
    time_closed_to: queryModel(String, 'closed_max', null),

    filters() {
      let filters_object = {};
      this.filter_list.forEach((f) => {
        if (this[f] != undefined) {
          if (f.startsWith('time')) {
            const date = new Date(this[f]);

            // The api handles full timestamps, thus to include issues created/closed during the day indicated we need to set the filter at the end of the same
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
        advanced_filters: this.advancedFilterQuery
          ? btoa(JSON.stringify(this.advancedFilterQuery))
          : null,
      };
    },
  },

  watch: {
    filters: {
      deep: true,
      handler: 'getIssues',
    },
  },

  created() {
    this.getIssues();
  },

  methods: {
    async resetFilters() {
      await this.$router.replace({ query: null });
      this.advancedFilters = [];
    },

    getIssues() {
      this.loading = true;
      this.$store
        .dispatch('getIssues', { with_links: true, ...this.filters })
        .then(() =>
          setTimeout(() => {
            this.loading = false;
          }, 1000),
        );
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
