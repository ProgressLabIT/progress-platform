<template>
  <div class="text-h5 q-mt-xl q-mb-md text-uppercase">
    {{ $t('phase.checklist_title') }}
  </div>

  <div id="checklist">
    <div
      v-for="(check, index) in step_checks"
      :key="index"
      class="q-py-md">
      <div
        class="row q-col-gutter-lg items-center"
        v-if="confirming_delete != index"
        @mouseenter="over_row = index"
        @mouseleave="over_row = null">
        <div class="col-1 text-center low-text">
          <q-icon
            v-if="edit_mode"
            name="mdi-drag-horizontal-variant"
            size="sm">
          </q-icon>
          <q-icon
            v-else
            name="mdi-checkbox-blank-outline"
            size="sm">
          </q-icon>
        </div>

        <div class="col-10">
          <q-input
            v-if="edit_mode"
            filled
            :model-value="check"
            @update:model-value="(value) => updateCheck(index, value)">
          </q-input>
          <div v-else>{{ check }}</div>
        </div>

        <div
          class="col-1 q-ml-auto"
          v-if="edit_mode && confirming_delete != index"
          v-show="over_row == index">
          <BaseTooltipIcon
            icon="mdi-delete"
            :tooltip="$capitalize($t('phase.delete_check'))"
            :color="$theme.red"
            @iconClick="confirming_delete = index">
          </BaseTooltipIcon>
        </div>
      </div>

      <!-- DELETE CONFIRMATION -->
      <q-card
        v-else
        square
        bordered
        class="background shadow-6 q-pa-md">
        <div class="row items-center text-body2 q-gutter-md">
          <span class="highlight">
            {{ check }}
          </span>
          <q-space />
          <span class="q-mr-md">
            {{ $capitalize($t('confirm_question')) }}
          </span>
          <q-btn
            padding="xs sm"
            icon="mdi-delete"
            color="theme-red"
            size="xs"
            @click.stop="deleteCheck(index)">
          </q-btn>
          <q-btn
            padding="xs sm"
            icon="mdi-close"
            color="theme-grey"
            size="xs"
            @click.stop="confirming_delete=null">
          </q-btn>
        </div>
      </q-card>
    </div>
  </div>

  <q-btn
    color="theme-blue"
    size="12px"
    class="q-mt-md"
    v-if="edit_mode"
    @click="addCheck">
    + {{ $capitalize($t('phase.add_check')) }}
  </q-btn>
</template>

<script>
// import {debounce as _debounce} from 'lodash/fp'
import BaseTooltipIcon from '@/components/BaseTooltipIcon.vue'
// import draggable from 'vuedraggable'

export default {

  name: 'StepChecklist',

  components: {
    BaseTooltipIcon,
    // draggable
  },

  props: ['phase_index', 'step_index', 'edit_mode'],

  data() {
    return {
      over_row: null,
      drag: false,
      confirming_delete: null
    }
  },

  computed: {

    product_key() {
      return this.$route.params.item_key
    },

    current_step() {
      let procedure = this.$store.state.process.temp[this.phase_index].steps
      return procedure[this.step_index]
    },

    step_checks: {
      get() {
        return this.current_step.checks
      },

      set(value) {
        let phase_index = this.phase_index
        let step_index = this.step_index

        this.$store.commit('UPDATE_STEP_DETAILS', { phase_index, step_index, field: 'checks', value })
      }
    }
  },

  methods: {

    addCheck() {
      let phase_index = this.phase_index
      let step_index = this.step_index

      let new_step = this.current_step
      new_step.checks.push('')
      // Handle cases in which step_checks is null

      this.$store.commit('ADD_OR_UPDATE_STEP', { phase_index, step_index, step_data: new_step })
    },

    updateCheck(index, text) {
      let phase_index = this.phase_index
      let step_index = this.step_index
      let new_checklist = this.step_checks
      new_checklist[index] = text
      console.log({new_checklist})
      this.$store.commit('UPDATE_STEP_DETAILS', { phase_index, step_index, field: 'checks', value: new_checklist })
    },

    deleteCheck(index) {
      let phase_index = this.phase_index
      let step_index = this.step_index
      let new_checklist = this.step_checks
      new_checklist.splice(index, 1)
      this.$store.commit('UPDATE_STEP_DETAILS', { phase_index, step_index, field: 'checks', value: new_checklist }) 
      this.confirming_delete = null
    }
  },
};
</script>

<style lang="css" scoped>
</style>
