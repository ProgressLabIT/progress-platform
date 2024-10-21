<template>
  <BaseModalScreen :show="true" @close="exit">
    <template #header>
      <span
        class="q-ml-md display medium highlight weight-medium text-uppercase"
      >
        {{ $t('work_order.key') }}: {{ wo_key }}
      </span>

      <div class="q-ml-auto col-auto">
        <q-tabs
          class="transparent text-low"
          active-class="text-high weight-bold"
          indicator-color="theme-blue"
          dense
        >
          <q-route-tab
            v-for="(page, index) in tabs"
            :key="index"
            :to="{ name: page, query: $route.query }"
            class="display"
          >
            {{ $t(`work_order.tabs.${page}`) }}
          </q-route-tab>
        </q-tabs>
      </div>
    </template>

    <template #content>
      <q-splitter
        v-if="vuex_ready"
        v-model="data_column_width"
        class="fit q-py-sm"
        separator-class="text-disabled"
      >
        <template #before>
          <WorkOrderDataColumn v-bind="{ wo_data }" />
        </template>

        <template #after>
          <router-view v-if="vuex_ready" v-slot="{ Component }">
            <keep-alive>
              <div class="full-height relative-position q-pl-sm">
                <component :is="Component" v-bind="{ wo_data }" />
              </div>
            </keep-alive>
          </router-view>
        </template>
      </q-splitter>

      <LoadingSignal v-else />
    </template>
  </BaseModalScreen>
</template>

<script>
import BaseModalScreen from '@/components/BaseModalScreen.vue';
import LoadingSignal from '@/components/LoadingSignal.vue';
import WorkOrderDataColumn from '@/components/WorkOrderDataColumn.vue';

export default {
  name: 'WorkOrderScreen',

  components: {
    BaseModalScreen,
    LoadingSignal,
    WorkOrderDataColumn,
  },

  props: {
    wo_key: {
      type: String,
      required: true,
    },
  },

  data() {
    return {
      show_modal: true,
      tabs: [
        'workOrderJobs',
        'workOrderIssues',
        'workOrderNotes',
        'workOrderMessages',
        'workOrderSerials',
        // 'workOrderHistory'
      ],
      vuex_ready: false,
      column_height: '80vh',
      events: undefined,
      data_column_width: 25,
    };
  },

  computed: {
    wo_data() {
      return this.$store.state.workorder.wo_data || { phase_sequence: [] };
    },
  },

  created() {
    this.get_wo_data();
    let eventURL =
      this.$api.defaults.baseURL + '/notification/global-notification';
    this.events = new EventSource(eventURL, {
      withCredentials: false,
    });
    this.events.addEventListener('global-notification', (event) => {
      this.handleMessage(event);
    });
  },

  beforeUnmount() {
    if (this.events) {
      this.events.close();
    }
  },

  methods: {
    handleMessage(message) {
      let event = JSON.parse(message.data);
      if (event.notification === 'REFRESH') {
        this.get_wo_data();
      }
    },
    exit() {
      let query = { ...this.$route.query };

      if (this.$route.query.back_to) {
        delete query.back_to;
        const push_route = { name: this.$route.query.back_to, query };
        this.$router.push(push_route);
      } else {
        this.$router.push({ name: 'workOrderList', query });
      }
    },

    get_wo_data() {
      Promise.all([
        this.$store.dispatch('loadWorkOrderData', this.wo_key),
        this.$store.dispatch('loadUsers'),
        this.$store.dispatch('getIssues', {
          work_order_key: this.wo_key,
          with_links: true,
        }),
      ]).then(() => (this.vuex_ready = true));
    },
  },
};
</script>
