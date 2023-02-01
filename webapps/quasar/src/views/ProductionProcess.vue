<template>
  <div class="row full-height q-py-md">

    <!-- ASIDE - PHASE LIST -->
    <div class="col-3 column full-height">
      <div class="q-px-lg">
        <div class="text-h1 display highlight">
          {{ product_data.code}}
        </div>
        <div class="text-body1">
          {{ product_data.description }}
        </div>

        <div class="text-h5 q-mt-xl q-mb-md text-uppercase">
          {{ $t('phase.long', 2) }}
        </div>
      </div>

      <q-tabs
        id="phases"
        class="transparent scroll medium text-left"
        active-class="highlight"
        align="left"
        shrink vertical dense
        indicator-color="transparent"
        v-model="current_phase">
        <q-tab
          v-for="(phase, index) in process"
          :key="phase._key"
          :name="index"
          :content-class="`full-width text-left ${edit_mode ? '' : 'undraggable'}`"
          @mouseenter="over_phase = index"
          @mouseleave="over_phase = null"
          @click="confirming_delete = null"
          style="max-height: 40px;">
          <div class="row items-center full-width q-px-md">
            <div class="col-1 q-mr-sm">
              <q-avatar
                size="20px"
                :color="current_phase == index ? 'theme-blue' : 'theme-grey'"
                class="display smaller"
                :class="{ highlight: current_phase == index }">
                {{ index + 1}}
              </q-avatar>
            </div>

            <div class="col-auto text-left text-truncate">
              <div class="display"
                :class="current_phase == index ? 'highlight' : 'text-low weight-medium'">
                {{ phase.alias }}
              </div>
            </div>

            <q-space />

            <div
              class="col-1"
              v-if="edit_mode"
              v-show="over_phase==index">
              <BaseTooltipIcon
                icon="mdi-delete"
                :tooltip="$t('phase.delete')"
                :color="$theme.red"
                @iconClick="confirming_delete = index">
              </BaseTooltipIcon>
            </div>
          </div>
        </q-tab>
      </q-tabs>

      <q-space />

      <!-- TODO: NEW PHASE OPERATION SELECTION -->


      <!-- ACTION BUTTONS -->
      <div class="q-px-md q-pb-sm">
        <q-btn
          v-if="!edit_mode"
          @click="toggleEdit"
          class="full-width"
          color="theme-blue">
          {{ $t('edit') }}
        </q-btn>

        <template v-else>
          <q-btn
            class="full-width q-mb-sm"
            color="theme-green"
            @click="saveChanges"
            :loading="saving">
            {{ $t('save') }}
          </q-btn>
          <q-btn
            class="full-width"
            color="theme-grey"
            @click="cancelChanges">
            {{ $t('cancel') }}
          </q-btn>
        </template>
      </div>

    </div>

    <!-- PHASE DETAILS -->
    <div class="col-9 q-pr-md">
      <q-tabs
        v-model="tab"
        class="transparent text-low display"
        active-class="highlight"
        align="right"
        shrink dense
        indicator-color="theme-blue">
        <q-tab
          v-for="(view, idx) in views"
          :key="idx"
          :name="idx">
          {{ $t(`views.${view}`) }}
        </q-tab>
      </q-tabs>
      <q-card square class="surface2 scroll" :style="`height: ${card_height}px`">
        <keep-alive>
          <Component
            :is="views[tab]"
            :phase="process[current_phase]"
            :product_data="product_data"
            :edit_mode="edit_mode">
          </Component>
        </keep-alive>
      </q-card>
    </div>
</div>
</template>

<script>
import { mapActions } from 'vuex'
import Sortable from 'sortablejs'

import PhaseParameters from '@/components/PhaseParameters.vue'
import PhaseSteps from '@/components/PhaseSteps.vue'
// import PhaseAssignments from '@/components/PhaseAssignments.vue'
import BaseTooltipIcon from '@/components/BaseTooltipIcon.vue'

const views_map = [
  'PhaseSteps', 
  'PhaseParameters',
  // 'PhaseAssignments' 
]

export default {

  name: 'ProductionProcess',

  components: {
    PhaseParameters,
    PhaseSteps,
    // PhaseAssignments,
    BaseTooltipIcon,
  },

  data() {
    return {
      views: views_map,
      tab:0,
      new_op: null,
      over_phase: null,
      confirming_delete: null,
      saving: false,
      drag: false,
    }
  },

  computed: {

    card_height() {
      return this.$q.screen.height - 114
    },
    
    product_key() {
      return this.$route.params.product_key
    }, 

    product_data() {
      return this.$store.getters.productData(this.product_key)
    },

    edit_mode: {
      get() {
        return this.$store.state.product.edit_modes.process
      },
      set(value) {
        this.$store.commit('TOGGLE_EDIT_MODE', { view: 'process', value })
      }
    },

    operations() {
      return this.$store.state.process.operations.slice().sort()
    },

    current_phase: {
      get() {
        return this.product_data.last_phase
      },

      set(value) {
        this.$store.commit(
          'UPDATE_PRODUCT_NAV_STATE', 
          { _key: this.product_key, last_phase: value}
        )
      }
    },

    process: {
      get() {
        return this.$store.state.process.temp
      },

      set(value) {
        this.$store.commit('UPDATE_PROCESS', value)
      }
    },

  },

  methods: {
    ...mapActions(['loadProductDetails']),

    toggleEdit() {
      this.edit_mode = true
    },

    cancelChanges() {
      const active_phase_key = this.process[this.current_phase]
      const original_process = this.$store.state.process.saved
      const original_phase_index = original_process.findIndex(p => p._key = active_phase_key)
      this.updateActivePhaseIndex({
        oldIndex: this.current_phase,
        newIndex: original_phase_index
      })
      this.$store.commit('CANCEL_PROCESS_CHANGES')
      this.confirming_delete = null
      this.edit_mode = false
      this.$emit('changes_canceled')
    },

    addPhase(new_operation) {
      let new_process = this.process
      new_process.push({ 
        alias: new_operation.name, 
        operation_key: new_operation._key, 
        product_key: this.product_key,
        params: new_operation.default_phase_parameters,
        steps: []
      })
      this.$store.commit('UPDATE_PROCESS', new_process)
      this.current_phase = new_process.length - 1

      // push blur to the end of the stack to let animation run properly
      setTimeout(() => {
        this.new_op = null
        this.$refs.add_phase.blur()
      }, 1)
    },

    deletePhase(phase_index) {
      this.$store.commit('DELETE_PHASE', phase_index)
      this.current_phase = this.process.length - 1
      this.confirming_delete = null
    },

    updateStepsMap(map) {
      this.$store.commit('UPDATE_PRODUCT_NAV_STATE', {
        _key: this.product_key,
        last_steps: map
      })
    },

    updateActivePhaseIndex({ oldIndex, newIndex }) {
      // Moved active phase
      if (this.current_phase == oldIndex) {
        this.current_phase = newIndex
      }
      // Moved earlier phase after active one
      else if ( oldIndex < this.current_phase
                && newIndex > this.current_phase ) {
        this.current_phase = this.current_phase - 1
      }
      // Moved later phase before active one
      else if ( oldIndex > this.current_phase
                && newIndex < this.current_phase ) {
        this.current_phase = this.current_phase + 1
      }

      // ADD HERE REORDERING OF last_steps MAP
      let new_steps_map = [...this.product_data.last_steps]
      const moved = new_steps_map.splice(oldIndex, 1)[0]
      new_steps_map.splice(newIndex, 0, moved)

      this.updateStepsMap(new_steps_map)
    },

    saveChanges() {
      this.saving = true
      let process_update = {
        product_key: this.product_key,
        new_process: this.process
      }
      this.$store.dispatch('saveTempProcess', process_update)
        .then(() => {
        // Show progress long enough the let user notice something is going on
        // even if the update is instantaneous
          setTimeout(() => {
            this.confirming_delete = null
            this.saving = false
            this.edit_mode = false
            this.$emit('changes_saved')
          }, 500)
        }).catch(err => {
          window.alert(err)
          this.saving = false
        })
    },
  },

  created() {
    const step_map = Array(this.process.length).fill(0)
    this.updateStepsMap(step_map)
  },

  mounted() {
    let container = document.querySelector("#phases .q-tabs__content")
    const _self = this
    Sortable.create(container, {
      ..._self.$store.state.drag_options,
      filter: '.undraggable',
      // use onEnd event provided by SortableJs library
      onEnd: ({ newIndex, oldIndex }) => {
        const moved = _self.process.splice(oldIndex, 1)[0]
        _self.process.splice(newIndex, 0, moved)
        _self.updateActivePhaseIndex({ oldIndex, newIndex })
      }
    })
  },

  watch: {
    confirming_delete() {
      const index = this.confirming_delete
      if (index != null) {
        const phase = this.process[index]
        this.$q.dialog({
          title: phase.alias,
          cancel: true,
          message: `Confermi di voler eliminare questa fase?`
        }).onOk(() => {
          this.deletePhase(index)
        }).onDismiss(() => {
          this.confirming_delete = null
        })
      }
    }
  }
};
</script>

<style lang="sass" scoped>
#phases .q-tab__content
  justify-content: left
</style>
