<template>
  <q-page-container class="absolute-full">
    <q-page class="row full-height">

      <!-- MAIN CONTENT -->
      <div class="column col full-height">
        <div class="row col-auto items-center justify-between q-pl-xs q-pr-md q-py-sm">

          <!-- TAB LINKS -->
          <q-tabs
            class="transparent text-low"
            active-class="text-high weight-bold"
            align="left"
            shrink
            dense
            indicator-color="theme-blue">
            <q-route-tab
              v-for="(view, index) in views"
              :key="index"
              :to="{ name: view.route_name, query: $route.query }"
              class="display">
              {{ $t(`views.${view.route_name}`) }}
            </q-route-tab>
          </q-tabs>

          <!-- NEW ISSUE BUTTON -->
          <q-btn
            size="0.75rem"
            :label="$t('new')"
            color="theme-blue"
            @click="show_issue_form = true">
          </q-btn>

           <IssueForm
            :show="show_issue_form"
            mode="new"
            with_links
            @close="show_issue_form = false">
          </IssueForm>
        </div>


        <!-- MAIN CONTENT -->
        <div class="col relative-position">
          <router-view :loading="loading"/>
        </div>
      </div>

      <!-- DIVIDER -->
      <q-separator vertical inset/>

      <!-- FILTERS -->
      <div class="col-3 full-height column q-px-lg">

        <!-- FILTERS HEADING -->
        <div class="col-auto row items-center justify-between q-mt-sm q-mb-md">
          <div class="col-auto highlight text-uppercase text-h5">
            {{ $t('filter', 2) }}
          </div>
          <!-- FILTERS RESET -->
          <div class="col-auto">
            <q-btn
              color="theme-blue"
              size="sm"
              padding="xs sm"
              v-show="filters_active"
              @click="resetFilters">
              <span>
                {{ $t('reset_filters') }}
              </span>
            </q-btn>
          </div>
        </div>

        <!-- FILTER FORM -->
      <div class="col scroll q-pb-xl">
          <div class="row q-col-gutter-md q-mb-md">
            <div class="col-6">
              <q-checkbox
                dense
                v-model="issue_open"
                :label="$t('issue_open')">
              </q-checkbox>
            </div>

            <div class="col-6">
              <q-checkbox
                dense
                v-model="issue_closed"
                :label="$t('issue_closed')">
              </q-checkbox>
            </div>

            <div class="col-6">
              <q-checkbox
                dense
                v-model="issue_critical"
                :label="$t('issue_critical')">
              </q-checkbox>
            </div>

            <div class="col-6">
              <q-checkbox
                dense
                v-model="issue_non_critical"
                :label="$t('issue_non_critical')">
              </q-checkbox>
            </div>
          </div>

          <!-- ISSUE KEY -->
          <q-input
            clearable
            filled
            dense
            hide-bottom-space
            autocomplete="off"
            name="search"
            debounce="1000"
            :label="$t('issue_key')"
            v-model="issue_key_search"
            class="q-mb-md">
            <template #append>
              <q-icon name="mdi-magnify" />
            </template>
          </q-input>

          <!-- ISSUE TYPE -->
          <BaseAutocompleteIssueType
            dense
            key_only
            class="q-mb-md"
            :value="issue_type_key"
            @select="selection => issue_type_key = selection">
          </BaseAutocompleteIssueType>


          <!-- OPENED DATE RANGE -->
          <div class="row q-col-gutter-sm">
            <div class="col">
              <q-input
                filled
                dense
                clearable
                debounce="1000"
                mask="date"
                v-model="time_created_from"
                :label="$t('opened_min')">
                <template #append>
                  <q-icon name="mdi-calendar" size="xs" class="cursor-pointer">
                    <q-popup-proxy cover transition-show="scale" transition-hide="scale">
                      <q-date minimal v-model="time_created_from">
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
                filled
                dense
                clearable
                mask="date"
                debounce="1000"
                v-model="time_created_to"
                :label="$t('opened_max')">
                <template #append>
                  <q-icon name="mdi-calendar" size="xs" class="cursor-pointer">
                    <q-popup-proxy cover transition-show="scale" transition-hide="scale">
                      <q-date minimal v-model="time_created_to">
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
                filled
                dense
                clearable
                mask="date"
                debounce="1000"
                v-model="time_closed_from"
                :label="$t('closed_min')">
                <template #append>
                  <q-icon name="mdi-calendar" size="xs" class="cursor-pointer">
                    <q-popup-proxy cover transition-show="scale" transition-hide="scale">
                      <q-date minimal v-model="time_closed_from">
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
                filled
                dense
                clearable
                mask="date"
                v-model="time_closed_to"
                debounce="1000"
                :label="$t('closed_max')">
                <template #append>
                  <q-icon name="mdi-calendar" size="xs" class="cursor-pointer">
                    <q-popup-proxy cover transition-show="scale" transition-hide="scale">
                      <q-date minimal v-model="time_closed_to">
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
            key_only
            :operator_only="false"
            :value="created_by"
            @select="(selection) => created_by = selection">
          </BaseAutocompleteUser>

          <!-- CLOSED BY -->
          <BaseAutocompleteUser
            :placeholder="$capitalize($t('closed_by'))"
            dense
            class="q-mb-md"
            key_only
            :operator_only="false"
            :value="closed_by"
            @select="(selection) => closed_by = selection">
          </BaseAutocompleteUser>

          <!-- OPERATION -->
          <BaseAutocompleteOperation
            dense
            filled
            class="q-mb-md"
            key_only
            :label="$capitalize($t('operation.label'))"
            :value="operation_key"
            @select="(selection) => operation_key = selection">
          </BaseAutocompleteOperation>

          <!-- PRODUCT -->
          <q-input
            clearable
            dense
            filled
            hide-bottom-space
            autocomplete="off"
            name="work_order"
            debounce="1000"
            class="q-mb-md"
            :label="$t('product.label')"
            v-model="product_code_search">
            <template #append>
              <q-icon name="mdi-magnify" />
            </template>
          </q-input>

          <!-- PHASE -->
          <q-input
            clearable
            dense
            filled
            hide-bottom-space
            autocomplete="off"
            name="work_order"
            debounce="1000"
            :label="$t('phase.short')"
            class="q-mb-md"
            v-model="phase_alias_search">
            <template #append>
              <q-icon name="mdi-magnify" />
            </template>
          </q-input>

          <!-- WORK ORDER -->
          <q-input
            clearable
            filled
            dense
            hide-bottom-space
            autocomplete="off"
            name="work_order"
            debounce="1000"
            :label="$capitalize($t('work_order.long'))"
            v-model="work_order_code_search"
            class="q-mb-md">
            <template #append>
              <q-icon name="mdi-magnify" />
            </template>
          </q-input>

          <!-- PROJECT -->
          <q-input
            clearable
            filled
            dense
            hide-bottom-space
            autocomplete="off"
            name="work_order"
            debounce="1000"
            :label="$capitalize($t('project'))"
            v-model="project_search"
            class="q-mb-md">
            <template #append>
              <q-icon name="mdi-magnify" />
            </template>
          </q-input>

          <div class="q-mb-xl"></div>

        </div>

        <div class="fade-bottom-bg"></div>

      </div>

    </q-page>
  </q-page-container>
</template>

<script>
import IssueForm from '@/components/IssueForm.vue'
import NoDataAlert from '@/components/NoDataAlert.vue'
import BaseAutocompleteIssueType from '@/components/BaseAutocompleteIssueType.vue'
import BaseAutocompleteOperation from '@/components/BaseAutocompleteOperation.vue'
import BaseAutocompleteProduct from '@/components/BaseAutocompleteProduct.vue'
import BaseAutocompleteUser from '@/components/BaseAutocompleteUser.vue'
import queryModel from '@/lib/queryModelFactory.js'

export default {

  name: 'QualityRoot',

  components: {
    BaseAutocompleteIssueType,
    BaseAutocompleteOperation,
    BaseAutocompleteProduct,
    BaseAutocompleteUser,
    IssueForm,
    NoDataAlert
  },

  data () {
    return {
      views: [
        { component: 'IssueOverview', route_name: 'issueOverview' }
      ],
      filter_list: ['issue_key_search', 'created_by','time_created_from','time_created_to','closed_by','time_closed_from','time_closed_to', 'issue_type_key', 'operation_key', 'work_order_code_search', 'product_code_search', 'phase_alias_search', 'project_search', 'issue_critical', 'issue_non_critical', 'issue_open', 'issue_closed'],
      bool_filters: ['issue_open', 'issue_closed', 'issue_critical', 'issue_non_critical'],
      loading: false,
      show_issue_form: false
    }
  },

  computed: {
    filters_active() {
      return this.filter_list.some(f => {
        return this.bool_filters.includes(f) ? this[f] === false : !!this[f]
      })
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
      let filters_object = {}
      this.filter_list.forEach(f => {
        if (this[f] != undefined) {
          if (f.startsWith('time')) {
            filters_object[f] = new Date(this[f]).toISOString()
          }
          else if (this.bool_filters.includes(f)) {
            if (this[f] == false) {
              filters_object[f] = this[f]
            }
          }
          else filters_object[f] = this[f]
        }
      })
      return filters_object
    }
  },

  methods: {
    resetFilters() {
      this.$router.replace({ query: null })
    },

    getIssues() {
      this.loading = true
      this.$store.dispatch('getIssues', { with_links: true, ...this.filters }).then(() => setTimeout(() => this.loading = false, 1000))
    }
  },

  created() {
    this.getIssues()
  },

  watch: {
    filters: {
      deep: true,
      handler: 'getIssues'
    }
  }
}
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
