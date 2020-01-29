<template>
  <v-container class="fill scroll">
    <v-row class="fill-height">
      <v-col cols="4" ref="step_list"
        class="d-flex flex-column px-6 fill">
        <h5>SEQUENZA PASSI</h5>

        <v-tabs
          vertical dark hide-slider grow
          v-model="current_steps_map[current_phase]"
          :color="$theme.whitehigh"
          background-color="transparent"
          class="mt-12"
          style="max-width: 100%"
          >

          <v-tab
            v-for="(step, index) in procedure"
            :key="index"
            class="d-flex justify-start align-center pl-1 pr-0"
            :class="current_steps_map[current_phase] == index ? 'weight-bold' : 'font-weight-regular'"
            style="width: 100%; height: 30px; text-transform: none !important; letter-spacing: normal"
            @mouseover="overRow=index"
            @mouseleave="overRow=null"
            >
            <v-row align="center" style="width: 100%" no-gutters class="pr-1">
              <v-col cols="1" class="mr-3">        
                <v-avatar
                  size="20"
                  :color="current_steps_map[current_phase] == index ? $theme.blue : $theme.grey"
                  class="d-flex text-center smaller weight-bold"
                  >{{ index + 1 }}
                </v-avatar>
              </v-col>  
              <v-col cols="9" class="text-left text-truncate">
                <span style="max-width: 80%">
                  {{ step.title }}
                </span>
              </v-col>
              <v-spacer></v-spacer>
              <v-col cols="1">
                <v-icon 
                  :id="`icon-${index}`"
                  class="ml-auto"
                  :color="current_steps_map[current_phase] == index ? $theme.whitehigh : $theme.whitelow">
                  {{ stepIcon(step.type) }}
                </v-icon>
              </v-col>    
            </v-row>    
           </v-tab>
        </v-tabs>
        <v-spacer></v-spacer>
        <div v-for="type in step_types" :key="type" class="d-flex justify-space-between">
          <button
            :color="$theme.whitehigh"
            class="py-1 weight-medium highlight"
            style="font-size: 14px">
            + Add {{ type }}
          </button>
          <v-icon class="ml-6">{{ stepIcon(type) }}</v-icon>
        </div>
      </v-col>  
      <v-divider vertical ></v-divider>
      <v-col 
        :style="`height: ${detail_box_height}`"
        class="px-6 scroll">

        <h5 class="mb-2">Titolo</h5>
        <v-text-field
          filled dense
          name="step_title"
          label="Titolo"
          single-line
          v-model="step_title"
          class="body-2"
        ></v-text-field>

        <h5 class="mb-2">Descrizione</h5>
        <v-textarea
          filled single-line dense auto-grow
          rows="2"
          row-height="36px"
          name="step_desc"
          label="Descrizione"
          :value="step_desc"
          @change="updateDesc($event)"
          class="body-2"
        ></v-textarea>


        <component 
          :is="step_component()" 
          :phase_no="current_phase" 
          :step_no="current_steps_map[current_phase]"
          class="mt-6"
          />

      </v-col>  
    </v-row>  
  </v-container>
</template>

<script>
import StepInstruction from '@/components/StepInstruction.vue'
import StepChecklist from '@/components/StepChecklist.vue'
import StepForm from '@/components/StepForm.vue'



export default {

  name: 'PhaseSteps',

  components: {
    StepInstruction,
    StepChecklist,
    StepForm
  },

  data() {
    return {
      step_types: ['instruction', 'checklist', 'form'],
      detail_box_height: '79vh',
      overRow: null,
    };
  },

  computed: {
    product_key() {
      return this.$route.params.item_key
    },

    productData() {
      return this.$store.getters.productData(this.product_key)
    },

    current_phase() {
      return this.productData.last_phase
    },

    current_steps_map: {
      get() {
        return this.productData.last_steps
      },

      set(value) {
        this.$store.commit(
          'UPDATE_PRODUCT', 
          { _key: this.product_key, last_steps: value}
        )
      }
    },

    procedure: {
      get() {
        return this.$store.state.current_product.process[this.current_phase].steps
      }
    },

    current_step() {
      const last_step_viewed = this.procedure[this.current_steps_map[this.current_phase]]
      return typeof last_step_viewed === 'undefined' ? 0 : last_step_viewed
    },

    step_title: {
      get() {
        return this.current_step.title
      },

      set(value) {
        let phase_no = this.current_phase
        let step_no = this.current_steps_map[phase_no]
        this.$store.commit('UPDATE_STEP_DETAILS', { phase_no, step_no, field: 'title', value })
      }
    },

    step_desc() {
        return this.current_step.description
    },
  },

  methods: {
    stepIcon(step_type) {
      switch (step_type) {
        case 'instruction': return 'playlist_add_check';
        case 'checklist': return 'mdi-format-list-checks';
        case 'form': return 'mdi-playlist-edit';
        default: return '';
      }
    },

    step_component() {

      let step = this.current_steps_map[this.current_phase] || 0

      switch (this.procedure[step].type) {
        case 'instruction': return 'StepInstruction';
        case 'checklist': return 'StepChecklist';
        case 'form': return 'StepForm';
        default: return '';
      }
    },

    updateDesc(value) {
      let phase_no = this.current_phase
      let step_no = this.current_steps_map[phase_no]
      // console.log(`Committing new description at phase ${phase_no}, step ${step_no}. New value: ${value}`)
      this.$store.commit('UPDATE_STEP_DETAILS', { phase_no, step_no, field: 'description', value })
    },
  },
};
</script>

<style lang="css" scoped>
</style>
