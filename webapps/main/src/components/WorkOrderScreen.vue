<template>
  <BaseModalScreen :show="true" @close="exit()">
    <template v-slot:header>
      <span class="q-ml-md display medium highlight weight-medium text-uppercase">
        {{ $t('work_order.key') }}: {{ wo_key }}
      </span>

      <div class="q-ml-auto col-auto">
        <q-tabs
          class="transparent text-low"
          active-class="text-high weight-bold"
          indicator-color="transparent"
          dense>
          <q-route-tab
            v-for="(page, index) in tabs" 
            :key="index" 
            :to="{ name: page, query: { back_to: $route.query.back_to } }"
            class="display" >
            {{ $t(`work_order.tabs.${page}`) }}
          </q-route-tab>
        </q-tabs>
      </div>
    </template>

    <template v-slot:content>
      <div class="fit shadow-6 row q-col-gutter-none">

        <template v-if="vuex_ready">

          <WorkOrderDataColumn
            v-if="vuex_ready"
            v-bind="{ wo_data }"
            class="col-4 col-lg-3 full-height">
          </WorkOrderDataColumn>

          <q-separator vertical inset />

          <router-view
            v-if="vuex_ready"
            v-bind="{ wo_data }"
            v-slot="{ Component }">
            <keep-alive>
              <div class="col full-height relative-position">
                <component :is="Component" />
              </div>
            </keep-alive>
          </router-view>

        </template>

        <LoadingSignal v-else />
      </div>
    </template>

  </BaseModalScreen>
</template>

<script>
import axios from 'axios'
import BaseModalScreen from '@/components/BaseModalScreen.vue'
import WorkOrderDataColumn from '@/components/WorkOrderDataColumn.vue'
import LoadingSignal from '@/components/LoadingSignal.vue'

export default {

  name: 'WorkOrderScreen',

  components: {
    BaseModalScreen,
    LoadingSignal,
    WorkOrderDataColumn,
  },

  props: ['wo_key'],

  data () {
    return { 
      show_modal: true,
      tabs: [
        'workOrderJobs',
        'workOrderIssues'
        // 'workOrderHistory'
      ],
      vuex_ready: false,
      column_height: '80vh',
      polling_instance: undefined
    }
  },

  computed: {
    wo_data() {
      return this.$store.state.workorder.wo_data || { phase_sequence: []}
    }
  },

  methods: {

    exit() {
      console.log('exit')
      if (this.$route.query.back_to) {
        this.$router.push({ name: this.$route.query.back_to })
      }
      else {
        this.$router.push({ name: 'workOrderList' })
      }
    },
    get_wo_data() {
      axios.all([
        this.$store.dispatch('loadWorkOrderData', this.wo_key),
        this.$store.dispatch('loadUsers')
      ])
      .then(() => this.vuex_ready = true)
    }
  },

  created() {
    this.get_wo_data()
    this.polling_instance = setInterval(this.get_wo_data, 10000)
  },

  beforeUnmount() {
    clearInterval(this.polling_instance)
  }
}
</script>

<style lang="css" scoped>
</style>
