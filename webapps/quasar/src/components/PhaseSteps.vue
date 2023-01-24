<template>
  <q-splitter class="full-height q-py-sm" :model-value="30">

    <template #before>
      <!-- STEP LIST -->
      <div class="col-4 column fit" ref="step_list">
        <div class="text-h5 text-uppercase q-px-lg q-my-md col-auto">
          {{ $t('step_sequence') }}
        </div>
        <div class="col-9 scroll" v-if="render_steps">
          <q-list dense id="steps">
            <q-item clickable v-ripple
              v-for="(step, index) in procedure"
              :key="step._key"
              :class="`${!edit_mode ? 'undraggable' : ''} ${ current_step_index == index ?  'highlight' : 'low-text'}`"
              @click="stepClick(index)">
              <q-item-section avatar class="col-auto">
              <q-avatar
                size="20px"
                :color="current_step_index == index ? 'theme-blue' : 'theme-grey'"
                class="smaller text-high q-ml-sm">
                {{ index + 1 }}
              </q-avatar>
              </q-item-section>
              <q-item-section class="text-truncate">
                {{ step.title.length ? step.title : '(nessun titolo)' }}
              </q-item-section>
              <q-item-section side class="q-mr-sm">
                <q-icon :name="stepIcon(step.type)" size="sm" class="q-ml-auto" :style="`color: ${ current_step_index == index ? $theme.text_high : $theme.text_low }`"/>
              </q-item-section>
            </q-item>
          </q-list>
        </div>

        <!-- NO STEPS -->
        <div v-else class="column q-mt-xl items-center">
          <q-icon name="mdi-alert-circle-outline" class="text-low q-mb-md" size="xl"/>
          <div class="text-h3 uppercase">
            {{ $t('phase.no_procedure') }}
          </div>
          <div class="text-body1">
            {{ $capitalize($t('phase.add_steps')) }}
          </div>
        </div>

        <!-- ADD STEPS -->
        <div v-if="edit_mode && typeof phase != 'undefined'" class="col-auto q-mt-auto q-mb-sm q-pl-sm q-pr-lg">
          <q-btn flat style="width: 105%;" size="12px" align="between" v-for="type in step_types" @click="addStep(type)">
            <span>+ {{ $t('add') }} {{ $t(`phase.step_types.${type}`) }}</span>
            <q-icon :name="stepIcon(type)" />
          </q-btn>
        </div>
      </div>
    </template>

    <!-- STEP DETAILS -->
    <template #after>
      <div v-if="render_steps" class="q-pa-md q-mx-md">

        <!-- STEP TITLE -->
        <div class="text-h5 uppercase q-mb-md">
          {{ $t('title') }}
        </div>
        <q-input
          v-if="edit_mode"
          filled dense
          name="step_title"
          :placeholder="$t('title')"
          v-model="step_title">
        </q-input>
        <div v-else class="q-mb-lg q-mt-md">
          {{ step_title }}
        </div>

        <!-- STEP DESCRIPTION -->
        <div class="text-h5 uppercase q-mt-lg q-mb-md">
          {{ $t('description') }}
        </div>
        <q-input
          v-if="edit_mode"
          filled dense
          type="textarea"
          name="step_desc"
          :placeholder="$t('description')"
          v-model="step_desc">
        </q-input>
        <div v-else class="q-mt-md">
          {{ step_desc }}
        </div>

        <component
          :is="step_component()"
          :phase_index="current_phase"
          :step_index="current_step_index"
          :edit_mode="edit_mode">
        </component>

        <!-- DELETE SECTION -->
        <div v-if="edit_mode" class="q-mb-md q-mt-xl">
          <template v-if="!confirming_delete">
            <span
              v-show="over_delete"
              class="display weight-bold q-mr-sm q-pa-sm bg-theme-red">
              {{ $t('delete') }}
            </span>
            <q-btn
              size="12px"
              icon="mdi-delete"
              color="theme-red"
              :label="$t('delete')"
              @click="showConfirmDelete">
            </q-btn>
          </template>

          <q-card v-else square class="bg-red-backdrop shadow-6 q-pa-md">
            <div class="row q-gutter-md flex-center">
              <span class="display medium highlight weight-bold">
                {{ $t('confirm_question') }}
              </span>

              <q-btn
                fab padding="sm"
                color="theme-grey"
                icon="mdi-close"
                @click="confirming_delete = false">
              </q-btn>

               <q-btn
                fab padding="sm"
                color="theme-red"
                icon="mdi-delete"
                @click="deleteStep(current_step_index)">
              </q-btn>
            </div>
          </q-card>
        </div>
        <!-- END OF DELETE SECTION -->
      </div>
    </template>
  </q-splitter>
</template>

<script>
import Sortable from 'sortablejs'

import StepInstruction from '@/components/StepInstruction.vue'
import StepChecklist from '@/components/StepChecklist.vue'
import StepForm from '@/components/StepForm.vue'

export default {

  name: 'PhaseSteps',

  props: ['edit_mode', 'phase', 'product_data'],

  components: {
    StepInstruction,
    StepChecklist,
    StepForm
  },

  data() {
    return {
      step_types: ['instruction', 'checklist', 'form'],
      detail_box_height: '79vh',
      over_delete: false,
      confirming_delete: false,
      drag: false,
    };
  },

  computed: {
    product_key() {
      return this.$route.params.product_key
    },

    current_phase() {
      return this.product_data.last_phase
    },

    current_steps_map: {
      get() {
        return this.product_data.last_steps
      },

      set(value) {
        this.$store.commit(
          'UPDATE_PRODUCT_NAV_STATE', 
          { _key: this.product_key, last_steps: value}
        )
      }
    },

    current_step_index: {
      get() {
        return this.current_steps_map[this.current_phase]
      },
      set(value) {
        this.current_steps_map[this.current_phase] = value
      }
    },

    procedure: {
      get() {
        return this.phase ? this.phase.steps : null
      },

      set(value) {
        let phase_index = this.current_phase
        this.$store.commit('UPDATE_PROCEDURE', { phase_index, procedure: value })
      }
    },

    render_steps() {
      return this.procedure != null && this.procedure.length
        ? true
        : false
    },

    current_step() {
      const last_step_viewed = this.procedure[this.current_step_index]
      return typeof last_step_viewed === 'undefined' ? 0 : last_step_viewed
    },

    step_title: {
      get() {
        return this.current_step.title
      },

      set(value) {
        this.updateStepData('title', value)
      }
    },

    step_desc: {
      get() {
        return this.current_step.description
      },
      set(value) {
        this.updateStepData('description', value)
      }
    },
  },

  methods: {
    stepIcon(step_type) {
      switch (step_type) {
        case 'instruction': return 'mdi-playlist-check';
        case 'checklist': return 'mdi-format-list-checks';
        case 'form': return 'mdi-playlist-edit';
        default: return '';
      }
    },

    step_component() {
      const step_index = this.current_steps_map[this.current_phase]
      const step = typeof step_index == 'undefined' ? 0 : step_index

      switch (this.procedure[step].type) {
        case 'instruction': return 'StepInstruction';
        case 'checklist': return 'StepChecklist';
        case 'form': return 'StepForm';
        default: return '';
      }
    },

    stepClick(index) {
      this.current_step_index = index
      this.confirming_delete = false
    },

    updateStepData(field, value) {
      let phase_index = this.current_phase
      let step_index = this.current_steps_map[phase_index]
      this.$store.commit('UPDATE_STEP_DETAILS', { phase_index, step_index, field, value })
    },

    addStep(type) {
      let phase_index = this.current_phase
      let step_index = this.procedure ? this.procedure.length : 0
      let step_data = {
        type: type,
        title: '',
        description: '', 
        checks: [],
        input_fields: [],
        media: []
      }
      this.$store.commit('ADD_OR_UPDATE_STEP', { phase_index, step_index, step_data})
      let new_step_index = this.procedure.length - 1
      this.current_step_index = new_step_index
    },

    showConfirmDelete() {
      this.confirming_delete = true
      this.over_delete = false
    },

    deleteStep(step_index) {
      const phase_index = this.current_phase
      const len = this.procedure.length
      // if step to be deleted is last, set next step index to second to last
      if (step_index == len-1) {
        const next_step_index = len > 1 ? len - 2 : 0
        this.current_steps_map[this.current_phase] = next_step_index
      }
      this.$store.commit('DELETE_STEP', { phase_index, step_index })
      this.confirming_delete = false

    },

    updateTabIndex({ oldIndex, newIndex }) {
      if (this.current_step_index == oldIndex) {
        this.current_steps_map[this.current_phase] = newIndex
      }
      else if ( oldIndex < this.current_step_index
                && newIndex > this.current_step_index ) {
        let new_step_index = this.current_step_index - 1
        this.current_steps_map[this.current_phase] = new_step_index
      }
      else if ( oldIndex > this.current_step_index
                && newIndex < this.current_step_index ) {
        let new_step_index = this.current_step_index + 1
        this.current_steps_map[this.current_phase] = new_step_index
      }
    },

    initSortable(container) {
      const _self = this
      Sortable.create(container, {
        ..._self.$store.state.drag_options,
        filter: '.undraggable',
        // use onEnd event provided by SortableJs library
        onEnd: ({ newIndex, oldIndex }) => {
          const moved = _self.procedure.splice(oldIndex, 1)[0]
          _self.procedure.splice(newIndex, 0, moved)
          _self.updateTabIndex({ oldIndex, newIndex })
        }
      })
    }
  },

  mounted() {
    let container = document.querySelector("#steps")
    if (container) {
      this.initSortable(container)
    }
  },
};
</script>

<style lang="sass" scoped>

</style>
