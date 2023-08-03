<template>
  <q-page-container class="absolute-full">
    <q-page class="row full-height">

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
        </div>


        <!-- MAIN CONTENT -->
        <div class="col relative-position">
          <router-view />
        </div>
      </div>

      <!-- DIVIDER -->
        <q-separator vertical inset/>

        <!-- FILTERS -->
        <div class="col-3 column q-px-lg">
          <div class="highlight text-uppercase text-h5 q-mt-sm q-mb-md">
            {{ $t('filter', 2) }}
          </div>

          <!-- OPENED BY -->
          <BaseAutocompleteUser
            :placeholder="$capitalize($t('opened_by'))"
            dense
            class="q-mb-md"
            key_only
            :operator_only="false"
            :value="filters.opened_by"
            @select="(selection) => filters.opened_by = selection">
          </BaseAutocompleteUser>

          <!-- CLOSED BY -->
          <BaseAutocompleteUser
            :placeholder="$capitalize($t('closed_by'))"
            dense
            class="q-mb-md"
            key_only
            :operator_only="false"
            :value="filters.closed_by"
            @select="(selection) => filters.closed_by = selection">
          </BaseAutocompleteUser>


          <!-- OPENED DATE RANGE -->
          <div class="row q-col-gutter-sm">
            <div class="col">
              <q-input
                filled
                dense
                clearable
                debounce="1000"
                mask="date"
                v-model="filters.opened_min"
                :label="$t('opened_min')">
                <template #append>
                  <q-icon name="mdi-calendar" size="xs" class="cursor-pointer">
                    <q-popup-proxy cover transition-show="scale" transition-hide="scale">
                      <q-date minimal v-model="filters.opened_min">
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
                v-model="filters.opened_max"
                :label="$t('opened_max')">
                <template #append>
                  <q-icon name="mdi-calendar" size="xs" class="cursor-pointer">
                    <q-popup-proxy cover transition-show="scale" transition-hide="scale">
                      <q-date minimal v-model="filters.opened_max">
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
          <div class="row q-col-gutter-sm q-mt-sm">
            <div class="col">
              <q-input
                filled
                dense
                clearable
                mask="date"
                debounce="1000"
                v-model="filters.closed_min"
                :label="$t('closed_min')">
                <template #append>
                  <q-icon name="mdi-calendar" size="xs" class="cursor-pointer">
                    <q-popup-proxy cover transition-show="scale" transition-hide="scale">
                      <q-date minimal v-model="filters.closed_min">
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
                v-model="filters.closed_max"
                debounce="1000"
                :label="$t('closed_max')">
                <template #append>
                  <q-icon name="mdi-calendar" size="xs" class="cursor-pointer">
                    <q-popup-proxy cover transition-show="scale" transition-hide="scale">
                      <q-date minimal v-model="filters.closed_max">
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

          <q-space />

          <q-btn
            color="theme-blue"
            v-show="filters_active"
            class="q-mb-md"
            @click="resetFilters">
            {{ $t('reset_filters') }}
          </q-btn>
        </div>
    </q-page>
  </q-page-container>
</template>

<script>
import NoDataAlert from '@/components/NoDataAlert.vue'
import BaseAutocompleteUser from '@/components/BaseAutocompleteUser.vue'
import queryModel from '@/lib/queryModelFactory.js'

export default {

  name: 'QualityRoot',

  components: {
    BaseAutocompleteUser,
    NoDataAlert
  },

  data () {
    return {
      views: [
        { component: 'IssueOverview', route_name: 'issueOverview' }
      ],
      filters: {
        opened_by: null,
        opened_min: null,
        opened_max: null,
        closed_by: null,
        closed_min: null,
        closed_max: null,
      }
    }
  },

  computed: {
    filters_active() {
      return Object.values(this.filters).some(v => !!v)
    }
  },

  methods: {
    resetFilters() {
      Object.keys(this.filters).forEach(f => this.filters[f] = null)
    }
  }
}
</script>
<style lang="css" scoped>
</style>
