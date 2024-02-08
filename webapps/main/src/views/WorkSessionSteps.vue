<template>
  <div ref="step_card" class="full-height column">
    <!-- NO PROCEDURE -->
    <NoDataAlert v-if="steps.length === 0">
      {{ $t('phase.no_procedure') }}
    </NoDataAlert>

    <template v-else>
      <q-toolbar dense class="col-1 q-pa-md shadow-4 surface2">
        <div
          ref="stepper"
          class="row full-width justify-between items-center q-col-gutter-xs"
        >
          <template v-for="(step, index) in steps" :key="step._key">
            <div class="col-auto q-px-xs">
              <q-avatar
                size="20px"
                :style="stepStyle(step._key)"
                class="row flex-center items-stretch text-center smaller text-weight-medium"
                @click="stepClick(step._key)"
              >
                <span
                  :class="
                    current_step_key === step._key
                      ? 'solid-white weight-bold'
                      : ''
                  "
                  class="smaller"
                >
                  {{ index + 1 }}
                </span>
              </q-avatar>
            </div>
            <hr
              v-if="index < steps.length - 1"
              :key="index"
              class="step-divider"
            />
          </template>
        </div>
      </q-toolbar>

      <keep-alive>
        <component
          :is="current_step.type === 'form' ? 'JobForm' : 'JobInstruction'"
          v-if="current_step"
          :key="current_step._key"
          :step="current_step"
        />
      </keep-alive>
    </template>
  </div>
</template>

<script>
import JobForm from '@/components/JobForm.vue';
import JobInstruction from '@/components/JobInstruction.vue';
import NoDataAlert from '@/components/NoDataAlert.vue';

export default {
  name: 'WorkSessionSteps',

  components: {
    JobInstruction,
    JobForm,
    NoDataAlert,
  },

  props: {
    job: {
      type: Object,
      required: true,
    },
  },

  data() {
    return {
      stepper_height: 0,
      step_content_height: 0,
    };
  },

  computed: {
    current_step_key: {
      get() {
        return this.$store.state.traceability.current_step_key;
      },
      set(key) {
        this.$store.state.traceability.current_step_key = key;
      },
    },

    steps() {
      return this.job.step_sequence;
    },

    current_step() {
      return this.steps.find(({ _key }) => _key === this.current_step_key);
    },

    batch_data() {
      return this.$store.state.traceability.current_batch_data.step_data;
    },

    force_order() {
      return this.job.parameters.step_check_force_order;
    },
  },

  methods: {
    stepStyle(stepKey) {
      const isStepActive = this.current_step_key === stepKey;
      const batchStep = this.batch_data?.find(({ _key }) => _key === stepKey);
      const isStepDone = batchStep?.done ?? false;
      const isStepCritical = batchStep?.critical ?? false;

      let backgroundColor = '';
      if (isStepCritical) {
        backgroundColor = isStepActive ? this.$theme.red : this.$theme.red_bg;
      } else if (isStepDone) {
        backgroundColor = isStepActive
          ? this.$theme.green
          : this.$theme.green_bg;
      } else if (isStepActive) {
        backgroundColor = this.job.active ? this.$theme.blue : this.$theme.grey;
      } else {
        backgroundColor = 'transparent';
      }

      return {
        backgroundColor,
        color: this.$theme.text_low,
        cursor: this.allowClick(stepKey) ? 'pointer' : 'not-allowed',
      };
    },

    allowClick(index) {
      if (!this.force_order || index === 0) {
        return true;
      }

      if (this.batch_data === undefined) {
        return false;
      }

      // First step is always allowed, start from second
      for (let i = 1; i < index; i++) {
        if (this.batch_data[i].done === false) {
          return false;
        }
      }

      return true;
    },

    stepClick(index) {
      if (this.allowClick(index)) {
        this.current_step_key = index;
      }
    },
  },
};
</script>
