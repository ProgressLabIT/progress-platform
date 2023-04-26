<template>
  <div class="row full-height q-py-md">

    <!-- ASIDE - PHASE LIST -->
    <div class="col-3 column full-height" style="min-width: 400px;">
      <div class="q-px-lg">
        <div class="text-h1 display highlight">
          {{ product_data.code}}
        </div>
        <div class="text-body1">
          {{ product_data.description }}
        </div>

        <div class="text-h5 q-mt-lg q-mb-sm text-uppercase">
          {{ $t('phase.long', 2) }}
        </div>
      </div>
      <q-separator inset></q-separator>

      <div class="scroll col q-py-sm full-width">
        <q-list
          id="phases"
          dense
          class="transparent medium text-left q-pl-sm"
          align="left"
          v-model="current_phase">
          <q-item
            v-for="(phase, index) in process"
            clickable
            v-ripple
            :key="phase._key"
            :name="index"
            :class="`full-width text-left ${edit_mode ? '' : 'undraggable'}`"
            @mouseenter="dragging ? undefined : over_phase = index"
            @mouseleave="dragging ? undefined : over_phase = null"
            @click="goToPhase(index)">
            <q-item-section avatar class="col-auto">
              <q-avatar
                size="20px"
                :color="current_phase == index ? 'theme-blue' : 'theme-grey'"
                class="display smaller"
                :class="{ highlight: current_phase == index }">
                {{ index + 1}}
              </q-avatar>
            </q-item-section>

            <q-item-section>
              <q-item-label
                class="display ellipsis"
                :class="current_phase == index ? 'highlight' : 'text-low weight-medium'">
                {{ phase.alias }}
              </q-item-label>
            </q-item-section>

            <q-item-section
              v-if="edit_mode"
              v-show="over_phase==index"
              side>
              <div class="row items-center">
                <BaseTooltipIcon
                  icon="mdi-pencil"
                  :tooltip="$t('rename')"
                  :color="$theme.blue"
                  @iconClick="update_alias_at_index = index">
                </BaseTooltipIcon>
                <BaseTooltipIcon
                  icon="mdi-delete"
                  :tooltip="$t('delete')"
                  :color="$theme.red"
                  @iconClick="confirming_delete = index">
                </BaseTooltipIcon>
              </div>
            </q-item-section>
          </q-item>

          <!-- PHASE ALIAS UPDATE PROMPT -->
          <BasePrompt
            :show="update_alias_at_index != null"
            :initial_value="update_alias_at_index ? process[update_alias_at_index].alias : null"
            :prompt="$t('phase.rename')"
            @update="updatePhaseAlias"
            @close="update_alias_at_index = null">
          </BasePrompt>
        </q-list>
      </div>

      <q-space />
      <q-separator inset></q-separator>

      <!-- ACTION BUTTONS -->
      <div class="column q-gutter-y-sm q-px-lg q-mt-sm q-pb-sm col-auto">
        <q-btn
          v-if="!edit_mode"
          @click="toggleEdit"
          class="full-width"
          color="theme-blue">
          {{ $t('edit') }}
        </q-btn>

        <template v-else>
          <BaseAutocompleteOperation
            @select="addPhase"
            :clearable="false">
          </BaseAutocompleteOperation>
          <q-btn
            class="full-width q-mt-md"
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
    <div class="col q-pr-md">
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
import BaseAutocompleteOperation from '@/components/BaseAutocompleteOperation.vue'
import PhaseParameters from '@/components/PhaseParameters.vue'
import PhaseSteps from '@/components/PhaseSteps.vue'
import PhaseNotes from '@/components/PhaseNotes.vue'
// import PhaseAssignments from '@/components/PhaseAssignments.vue'
import BasePrompt from '@/components/BasePrompt.vue'
import BaseTooltipIcon from '@/components/BaseTooltipIcon.vue'

const views_map = [
  'PhaseSteps', 
  'PhaseParameters',
  'PhaseNotes'
  // 'PhaseAssignments' 
]

export default {

  name: 'ProductionProcess',

  components: {
    PhaseParameters,
    PhaseSteps,
    PhaseNotes,
    // PhaseAssignments,
    BasePrompt,
    BaseTooltipIcon,
    BaseAutocompleteOperation
  },

  data() {
    return {
      views: views_map,
      tab:0,
      new_op: null,
      over_phase: null,
      confirming_delete: null,
      update_alias_at_index: null,
      saving: false,
      dragging: false,
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

    goToPhase(index) {
      this.confirming_delete = null
      this.current_phase = index
    },

    cancelChanges() {
      const active_phase = this.process[this.current_phase]
      if (active_phase) {
        const original_process = this.$store.state.process.saved
        const original_phase_index = original_process.findIndex(p => p._key = active_phase._key)
        this.updateActivePhaseIndex({
          oldIndex: this.current_phase,
          newIndex: original_phase_index
        })
      }

      this.$store.commit('CANCEL_PROCESS_CHANGES')
      this.confirming_delete = null
      this.edit_mode = false
      this.$emit('changes_canceled')
    },

    addPhase(new_operation) {
      let new_process = this.process
      new_process.push({ 
        // Add temp _key so that sorting works with new phases too
        _key: Date.now(),
        alias: new_operation.name, 
        operation_key: new_operation._key, 
        product_key: this.product_key,
        params: new_operation.default_phase_parameters,
        steps: []
      })
      this.process = new_process
      this.current_phase = new_process.length - 1
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
                && newIndex >= this.current_phase ) {
        this.current_phase --
      }
      // Moved later phase before active one
      else if ( oldIndex > this.current_phase
                && newIndex <= this.current_phase ) {
        this.current_phase ++
      }

      // ADD HERE REORDERING OF last_steps MAP
      let new_steps_map = [...this.product_data.last_steps]
      const moved = new_steps_map.splice(oldIndex, 1)[0]
      new_steps_map.splice(newIndex, 0, moved)

      this.updateStepsMap(new_steps_map)
    },

    updatePhaseAlias(value) {
      this.process[this.update_alias_at_index].alias = value.toUpperCase()
      this.update_alias_at_index = null
    },

    saveChanges() {
      this.saving = true
      let process_update = {
        product_key: this.product_key,
        new_process: this.process.map(p => {
          // remove temp _key
          if (typeof p._key == 'number') {
            delete p._key
          }
          return p
        })
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

  mounted() {
    // Create step map
    const step_map = Array(this.process.length).fill(0)
    this.updateStepsMap(step_map)

    // Initialize draggable phases
    let container = document.querySelector("#phases")
    const _self = this
    Sortable.create(container, {
      ..._self.$store.state.drag_options,
      filter: '.undraggable',
      onStart: () => _self.dragging = true,
      // use onEnd event provided by SortableJs library
      onEnd: ({ newIndex, oldIndex }) => {
        _self.dragging = false
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
