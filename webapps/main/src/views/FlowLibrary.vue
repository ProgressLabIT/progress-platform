<template>
  <q-list class="q-pr-xl scroll">
    <q-item v-for="flow in flows" :key="flow.id">
      <q-item-section top class="q-pa-md col-5 q-pr-xl">
        <q-item-label class="text-h4 highlight">{{ flow.name }}</q-item-label>
        <q-item-label caption>{{ flow.description }}</q-item-label>
      </q-item-section>
      <q-item-section top class="q-pa-md q-mr-xl">
        <div class="row q-pt-md q-col-gutter-md">
          <div v-for="field in flow.parameters" :key="field.title" class="col">
            <q-input
              v-model="field.value"
              stack-label
              label-slot
              filled
              hide-bottom-space
              :placeholder="field.default"
              :label="
                field.title +
                ' (' +
                field.type +
                ')' +
                (field.required ? ' - REQUIRED' : '')
              "
            >
            </q-input>
          </div>
        </div>
      </q-item-section>
      <q-item-section class="col-auto">
        <q-btn label="launch" color="theme-blue" @click="run(flow)" />
      </q-item-section>
    </q-item>

    <BaseDialog :show="!!launched_flow">
      <q-card class="surface1 q-pa-md" style="min-width: 60vw">
        <!-- FLOW TITLE -->
        <q-card-section class="row justify-between items-center">
          <div class="text-h3">{{ launched_flow }}</div>
          <q-chip class="q-ml-md row items-center" :color="state_color">
            <div class="q-mr-sm">{{ flow_state }}</div>
            <q-spinner-hourglass
              v-if="['SCHEDULED', 'PENDING'].includes(flow_state)"
            />
            <q-spinner-dots v-else-if="flow_state === 'RUNNING'" />
            <q-icon
              v-else-if="failed_states.includes(flow_state)"
              name="mdi-close-octagon"
            />
            <q-icon v-else name="mdi-check-circle" />
          </q-chip>
        </q-card-section>

        <!-- LOGS -->
        <q-card-section>
          <div
            id="flow-log"
            class="background smaller full-with scroll relative-position q-pa-md"
            style="height: 400px; font-family: monospace; white-space: pre-line"
          >
            <q-list dense>
              <q-item v-for="(l, index) in flow_logs" :key="index" class="q-mb-sm">
                <q-item-section class="text-disabled">
                  {{ l.timestamp }}
                </q-item-section>
                <q-item-section>
                  {{ l.message }}
                </q-item-section>
              </q-item>
            </q-list>
            <div id="scroll-anchor" class="q-mb-sm">
              <q-spinner v-if="active_states.includes(flow_state)" />
              <q-badge v-else color="theme-grey">END</q-badge>
            </div>
          </div>
        </q-card-section>

        <q-card-section
          v-if="!active_states.includes(flow_state)"
          class="row justify-end"
        >
          <q-btn
            :label="$t('close')"
            color="theme-grey"
            @click="clearFlowData"
          />
        </q-card-section>
      </q-card>
    </BaseDialog>
  </q-list>
</template>

<script>
import BaseDialog from '@/components/BaseDialog.vue';

export default {
  name: 'FlowLibrary',

  components: {
    BaseDialog,
  },

  data() {
    return {
      flows: [],
      active_states: ['SCHEDULED', 'PENDING', 'RUNNING'],
      failed_states: ['FAILED', 'CRASHED'],
      launched_flow: false,
      run_id: null,
      polling_instance: null,
      flow_logs: [],
      flow_state: null,
      flow_query_filter: {
        query: {
          deployments: {
            work_queue_name: {
              eq_: 'integration',
            },
          },
        },
      },
    };
  },

  computed: {
    base_url() {
      return 'http://' + window.location.hostname + ':4200/api';
    },

    deployments_url() {
      return this.base_url + '/deployments/filter';
    },

    flows_url() {
      return this.base_url + '/flows/filter';
    },

    status() {
      return {
        url: this.base_url + '/flow_runs/filter',
        body: {
          flow_runs: {
            id: { any_: [this.run_id] },
          },
        },
      };
    },

    state_color() {
      switch (this.flow_state) {
        case 'PENDING':
        case 'SCHEDULED':
          return 'theme-orange';

        case 'RUNNING':
          return 'theme-blue';

        case 'COMPLETED':
          return 'theme-green';

        default:
          return 'theme-red';
      }
    },

    logs() {
      return {
        url: this.base_url + '/logs/filter',
        body: {
          logs: {
            level: { ge_: 0 },
            flow_run_id: { any_: [this.run_id] },
          },
          sort: 'TIMESTAMP_ASC',
          offset: this.flow_logs.length,
        },
      };
    },

    flow_list() {
      if (this.flows) {
        return;
      } else {
        return [];
      }
    },
  },

  created() {
    this.fetchFlows();
  },

  methods: {
    defineFlowParameters(deployment_data) {
      const params_data = deployment_data.parameter_openapi_schema;
      const required_list = params_data.required || [];
      const flow_params = Object.values(params_data.properties).map((p) => {
        return {
          ...p,
          required: required_list.includes(p.title),
          value: p.default, // can be undefined
        };
      });
      return flow_params;
    },

    fetchFlows() {
      // Get flow name from flows. Deployment data provides parameters and endpoint info
      const calls = [
        this.$axios.post(this.flows_url, this.flow_query_filter),
        this.$axios.post(this.deployments_url, this.flow_query_filter),
      ];
      Promise.all(calls).then((responses) => {
        const flows_data = responses[0].data;
        const deployments_data = responses[1].data;
        this.flows = flows_data.map((f) => {
          const deployment = deployments_data.find((d) => d.flow_id == f.id);
          return {
            ...f,
            deployment_id: deployment.id,
            description: deployment.description,
            parameters: this.defineFlowParameters(deployment),
          };
        });
      });
    },

    run(flow_data) {
      const url =
        this.base_url +
        '/deployments/' +
        flow_data.deployment_id +
        '/create_flow_run';
      let params_data = {};
      flow_data.parameters.forEach((p) => (params_data[p.title] = p.value));

      const body = {
        state: {
          type: 'SCHEDULED',
        },
        parameters: params_data,
      };
      this.$axios.post(url, body).then((resp) => {
        this.launched_flow = flow_data.name;
        this.flow_state = resp.data.state.type;
        this.run_id = resp.data.id;
        this.polling_instance = setInterval(this.checkRun, 1000);
      });
    },

    async updateLogs(log_resp) {
      const new_logs = log_resp.data.map((l) => {
        // Keep only the time part of the timestamp, remove the date and timezone
        const timestamp = l.timestamp.split('T')[1].split('+')[0];
        // Replace newlines with <br>
        const message = l.message.replace(/\n/, '<br>');
        return { timestamp, message };
      });
      const logbox = document.getElementById('flow-log');
      this.flow_logs.push(...new_logs);
      logbox.scrollTop = logbox.scrollHeight;
    },

    async checkRun() {
      const [status, logs] = await this.$axios.all([
        this.$axios.post(this.status.url, this.status.body),
        this.$axios.post(this.logs.url, this.logs.body),
      ]);
      this.flow_state = status.data[0].state_type;
      this.updateLogs(logs);

      if (['COMPLETED', 'FAILED', 'CRASHED'].includes(this.flow_state)) {
        clearInterval(this.polling_instance);
      }
    },

    clearFlowData() {
      this.launched_flow = null;
      this.flow_logs = [];
      this.flow_state = null;
    },
  },
};
</script>

<style lang="sass" scoped>
#flow-log *
  overflow-anchor: none !important

#scroll-anchor
  overflow-anchor: auto
  height: 1px
</style>
