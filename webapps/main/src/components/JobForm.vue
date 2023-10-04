<template>
  <div class="col column q-pt-xl q-px-xl">

    <!-- FORM TITLE -->
    <div class="col-auto">
      <div class="text-h3 q-px-none q-pt-none nowrap">
        {{ step.title }}
      </div>
      <div class="text-body2 text-low">
        {{ step.description }}
      </div>
    </div>

    <!-- FORM BODY -->
    <q-scroll-area class="col q-mt-lg q-pr-md">
      <div
        v-for="(field, index) in step_form"
        :key="index"
        class="q-mb-lg">
        <q-input
          v-if="field.type=='short'"
          input-class="text-low"
          filled square
          :model-value="field_data[index]"
          @update:model-value="updateField(index, $event)"
          debounce="500"
          :disabled="!job_active  || batch_step.done"
          :label="field.name"
          :key="index">
        </q-input>
        <q-input
          v-if="field.type=='long'"
          input-class="text-low"
          filled square
          :model-value="field_data[index]"
          debounce="500"
          @update:model-value="updateField(index, $event)"
          :disabled="!job_active || batch_step.done"
          :label="field.name"
          :key="index"
          type="textarea">
        </q-input>
      </div>
    </q-scroll-area>
  </div>
</template>

<script>
import { debounce as _debounce } from 'lodash'
export default {

  name: 'JobForm',

  props: {
    step: {
      type: Object,
      required: true,
    },
  },

  data () {
    return {
      // values: []
    }
  },

  computed: {
    step_form() {
      return this.step.input_fields
    },

    job_active() {
      return this.$store.state.traceability.working_job_data.active
    },

    batch_step() {
      return this.$store.getters.getBatchStep(this.step._key)
    },

    field_data() {
      const data = this.batch_step.user_data
      return data ? data : []
    }
  },

  methods: {
    updateField(index, value) {
      const field_data = {
        step_key: this.step._key,
        value_index: index,
        value
      }
      this.$store.commit('UPDATE_STEP_USER_DATA', field_data)
    }
  },

  created() {
    this.debouncedFieldUpdate = _debounce(this.updateField, 1000)
  }
}
</script>

<style lang="css" scoped>
</style>
