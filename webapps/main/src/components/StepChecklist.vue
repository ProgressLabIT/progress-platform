<template>
  <div>
    <h5 class="mb-6 text-uppercase">Lista di controllo</h5>
    <draggable v-model="step_checks">
      <v-row no-gutters 
        v-for="(check, index) in step_checks" 
        :key="index"
        @mouseover="overRow=index"
        @mouseleave="overRow=null">
        <v-col cols="11">  
          <v-textarea 
            filled single-line dense auto-grow
            rows="1"
            row-height="36px"
            name="step_desc"
            label="Descrizione"
            :value="check"
            @change="udpateCheck(index, $event)"
            class="body-2"
            >
            <template v-slot:prepend>
              <v-icon :color="$theme.whitelow">check_box_outline_blank</v-icon>
            </template>
          </v-textarea> 
        </v-col>  
        <v-spacer></v-spacer>
        <v-col class="pt-2" v-show="overRow==index">
          <TooltipIcon
            icon="delete"
            tooltip="Rimuovi controllo"
            :color="$theme.red"
            @iconClick="deleteCheck(index)"/>
        </v-col>  
      </v-row>  
    </draggable>
    <button
        :color="$theme.whitehigh"
        class="py-1 weight-medium highlight"
        style="font-size: 14px"
        @click="addCheck">
        + Aggiungi controllo
    </button>
  </div>
</template>

<script>
// import {debounce as _debounce} from 'lodash/fp'
import TooltipIcon from '@/components/TooltipIcon'
import draggable from 'vuedraggable'

export default {

  name: 'StepChecklist',

  components: {
    TooltipIcon,
    draggable
  },

  props: ['phase_no', 'step_no'],

  data() {
    return {
      overRow: null
    }
  },

  computed: {

    product_key() {
      return this.$route.params.item_key
    },

    current_step() {
      let procedure = this.$store.state.current_product.process[this.phase_no].steps
      return procedure[this.step_no]
    },

    step_checks: {
      get() {
        return this.current_step.checks
      },

      set(value) {
        let phase_no = this.phase_no
        let step_no = this.step_no

        this.$store.commit('UPDATE_STEP_DETAILS', { phase_no, step_no, field: 'checks', value })
      }
    }
  },

  methods: {

    addCheck() {
      let phase_no = this.phase_no
      let step_no = this.step_no

      let new_step = this.current_step
      new_step.checks.push('')
      // Handle cases in which step_checks is null

      this.$store.commit('ADD_OR_UPDATE_STEP', { phase_no, step_no, step_data: new_step })
    },

    udpateCheck(index, text) {
        let phase_no = this.phase_no
        let step_no = this.step_no
        let new_checklist = this.step_checks
        new_checklist[index] = text
        this.$store.commit('UPDATE_STEP_DETAILS', { phase_no, step_no, field: 'checks', value: new_checklist })
    },

    deleteCheck(index) {
      let phase_no = this.phase_no
      let step_no = this.step_no
      let new_checklist = this.step_checks
      new_checklist.splice(index, 1)
      this.$store.commit('UPDATE_STEP_DETAILS', { phase_no, step_no, field: 'checks', value: new_checklist }) 
    }
  },
};
</script>

<style lang="css" scoped>
</style>
