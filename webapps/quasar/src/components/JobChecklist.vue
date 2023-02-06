<template>
  <div class="col column q-pt-lg q-px-xl">
    
    <!-- CHECKLIST TITLE -->
    <div class="col-auto q-pt-md">
      <div class="text-h3 display q-px-none q-pt-none nowrap">
        {{ step.title }}
      </div>
      <div class="text-body2 text-low">
        {{ step.description }}
      </div>
    </div>

    <!-- CHECKS -->
    <q-scroll-area class="col q-mt-md">
      <template v-for="(check, index) in step_checks" :key="`row${index}`">
        <div class="row items-center q-py-md">
          <div class="col-1 items-center">
            <q-avatar
              :color="Math.abs(values[index])==1 ? 'theme-green' : 'transparent'"
              size="24px"
              class="row flex-center text-center text-body2 font-weight-medium">
              <span v-if="!values[index]">
                {{ index + 1 }}
              </span>
              <q-icon v-else small class="solid-white" name="mdi-check" />
            </q-avatar>
          </div>
          <div class="col-6 items-center">
            <p class="text-body1 q-ma-none">{{ check }}</p>
          </div>
          <q-space />
          <div class="col-auto">
            <q-btn
              :key="`no${index}`"
              size="lg" unelevated
              :flat="values[index]!=-1"
              :disabled="!job_active || batch_step.done"
              color="theme-red"
              style="width: 100px"
              @click="toggleCheck(index, -1)">
              <span class="text-h4 display weight-bold">{{ $t('no') }}</span>
            </q-btn>
            <q-btn
              size ="lg" unelevated
              :key="`yes${index}`"
              :disabled="!job_active || batch_step.done"
              :flat="values[index]!=1"
              color="theme-green"
              style="width: 100px"
              @click="toggleCheck(index, 1)"
              class="q-ml-lg">
              <span class="text-h4 display weight-bold">{{ $t('yes') }}</span>
            </q-btn>
          </div>
        </div>
        <q-separator
          :key="`divider${index}`"
          v-if="index < step_checks.length -1">
        </q-separator>
      </template>
    </q-scroll-area>
  </div>
</template>

<script>
export default {

  name: 'JobChecklist',

  props: {
    step: {
      type: Object,
      required: true,
    },
    height: {
      type: Number,
    }
  },

  data () {
    return {
      // values: []
    }
  },

  computed: {
    step_checks() {
      return this.step.checks
    },

    job_active() {
      return this.$store.state.traceability.working_job_data.active
    },

    batch_step() {
      return this.$store.getters.getBatchStep(this.step._key)
    },
    
    values() {
      const data = this.batch_step.user_data
      return data ? data : []
    },
  },

  methods: {
    toggleCheck(index, check_value) {
      // reset check value to 0 when user clicks a second time on the choice made
      let value = check_value
      if (this.values[index] == check_value) {
        value = 0
      }

      const check_data = {
        step_key: this.step._key,
        value_index: index,
        value
      }
      this.$store.commit('UPDATE_STEP_USER_DATA', check_data)
    },
  },

  created() {
    // this.step_checks.forEach(() => this.values.push(0))
  }
}
</script>

<style lang="css" scoped>
</style>
