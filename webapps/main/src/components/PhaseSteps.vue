<template>
  <v-container class="fill scroll">
    <v-row class="fill">
      <v-col cols="4" class="d-flex flex-column px-6 scroll">
        <h5>DETTAGLIO FASE</h5>

        <v-tabs
          vertical dark hide-slider grow
          v-model="current_steps[current_phase]"
          :color="$theme.whitehigh"
          background-color="transparent"
          class="mt-12"
          >

          <v-tab
            v-for="(step, index) in procedure"
            :key="index"
            class="d-flex justify-start align-center pl-1 pr-0"
            :class="current_steps[current_phase] == index ? 'weight-bold' : 'font-weight-regular'"
            style="height: 30px; text-transform: none !important; letter-spacing: normal"
            >
              
            <v-avatar
              size="20"
              :color="current_steps[current_phase] == index ? $theme.blue : $theme.grey"
              class="d-flex text-center smaller weight-bold mr-3"
              >{{ index + 1 }}
            </v-avatar>
            <span class="mr-12 nowrap">
              {{ step.title }}
            </span>
            <v-icon 
              :id="`icon-${index}`"
              class="ml-auto">
              {{ stepIcon(step.type) }}
            </v-icon>
           </v-tab>
        </v-tabs>
        <v-spacer></v-spacer>
        <div v-for="type in step_types" :key="type" class="d-flex justify-space-between">
          <span text
            :color="$theme.whitehigh"
            class="py-1 weight-medium highlight"
            style="font-size: 14px">
            + Add {{ type }}
          </span>
          <v-icon class="ml-6">{{ stepIcon(type) }}</v-icon>
        </div>
      </v-col>  
      <v-divider inset vertical ></v-divider>
      <v-col>
        <component :is="step_component()" :step="current_steps[current_phase]"/>
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

  props: ['current_phase'],

  components: {
    StepInstruction,
    StepChecklist,
    StepForm
  },

  data() {
    return {
      mouseOverStep: [],
      step_types: ['instruction', 'checklist', 'form']
    };
  },

  computed: {
    product_key() {
      return this.$route.params.item_key
    },

    procedure: {
      get() {
        return this.$store.state
                            .current_product
                            .process_data[this.current_phase]
                            .steps
      }
    },

    current_steps: {
      get() {
        let product = this.$store.state.products.find(p => p._key == this.product_key)
        return product.last_steps
      },

      set(value) {
        this.$store.commit(
          'UPDATE_PRODUCT', 
          { _key: this.product_key, last_steps: value}
        )
      }
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

    showIcon(index) {
      // document.getElementById(`icon-${index}`).classList.remove('transparent')
      return this.mouseOverStep[index]

    },

    hideIcon(index) {
      // document.getElementById(`icon-${index}`).classList.add('transparent')      
      this.mouseOverStep[index] = false
    },

    step_component() {
      let procedure = this.procedure
      console.log("getting step component...")
      console.log('Procedure: ')
      console.log(JSON.stringify(procedure))
      console.log('Current Step: ' + this.current_steps[this.current_phase])

      let step = this.current_steps[this.current_phase] || 0

      switch (this.procedure[step].type) {
        case 'instruction': return 'StepInstruction';
        case 'checklist': return 'StepChecklist';
        case 'form': return 'StepForm';
        default: return '';
      }
    }
  }
};
</script>

<style lang="css" scoped>
</style>
