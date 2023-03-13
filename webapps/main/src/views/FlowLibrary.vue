<template>
  <q-list class="q-pr-xl scroll">
    <q-item v-for="flow in flows" :key="flow.id">
      <q-item-section top class="q-pa-md col-5 q-pr-xl">
        <q-item-label class="text-h4 highlight">{{ flow.name }}</q-item-label>
        <q-item-label caption>{{ flow.description }}</q-item-label>
      </q-item-section>
      <q-item-section top class="q-pa-md q-mr-xl">
        <div class="row q-pt-md q-col-gutter-md">
          <div
            class="col"
            v-for="field in flow.parameters"
            :key="field.title">
            <q-input
              v-model="field.value"
              stack-label
              label-slot
              filled
              hide-bottom-space
              :placeholder="field.default"
              :label="field.title + ' (' + field.type + ')' + (field.required ? ' - REQUIRED' : '')">
            </q-input>
          </div>
        </div>
      </q-item-section>
      <q-item-section class="col-auto">
        <q-btn @click="print(flow)" label="launch" color="theme-blue"/>
      </q-item-section>
    </q-item>
  </q-list>
</template>

<script>
export default {

  name: 'FlowLibrary',

  data () {
    return {
      base_url: 'http://192.168.2.189:4200/api',
      flows: [],
      query_filter: {
        "query": {
          "deployments": {
            "work_queue_name": {
              "eq_": "integration"
            }
          }
        }
      }
    }
  },

  computed: {
    deployments_url() {
      return this.base_url + '/deployments/filter'
    },

    flows_url() {
      return this.base_url + '/flows/filter'
    },

    flow_list() {
      if (this.flows) {
        return
      }
      else return []
    }
  },

  methods: {
    defineFlowParameters(deployment_data) {
      const params_data = deployment_data.parameter_openapi_schema
      const required_list = params_data.required || []
      const flow_params = Object.values(params_data.properties).map(p => {
        return {
          ...p,
          required: required_list.includes(p.title),
          value: p.default // can be undefined
        }
      })
      return flow_params
    },

    print(flow_data) {
      console.log({ flow_data })
    }
  },

  created() {
    let flows_data, deployment_data
    const calls = [
      this.$axios.post(this.flows_url, this.query_filter),
      this.$axios.post(this.deployments_url, this.query_filter)
    ]
    this.$axios.all(calls).then(responses => {
      const flows_data = responses[0].data
      const deployments_data = responses[1].data
      this.flows = flows_data.map(f => {
        const deployment = deployments_data.find(d => d.flow_id == f.id)
        return {
          ...f,
          deployment_id: deployment.id,
          description: deployment.description,
          parameters: this.defineFlowParameters(deployment)
        }
      })
    })
  }
}
</script>

<style lang="css" scoped>
</style>
