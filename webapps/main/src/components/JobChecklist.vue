<template>
  <v-container fluid class="scroll pt-12 px-12" :style="'max-height:'+height+'px'">
    <template v-for="(check, index) in step_checks" >
      <v-row 
        :key="`row${index}`"
        align="center">
        <v-col cols="1" class="d-flex align-center">
          <v-avatar 
            :color="Math.abs(values[index])==1 ? $theme.green : 'transparent'" 
            size="24" 
            class="d-flex text-center body-2 font-weight-medium">
            <span v-if="!values[index]">
              {{ index + 1 }}
            </span>
            <v-icon v-else small class="solid-white">mdi-check</v-icon>
          </v-avatar> 
        </v-col>
        <v-col cols="6" class="d-flex align-center">
          <p class="highlight ma-0">{{ check }}</p>
        </v-col>
        <v-spacer></v-spacer>
        <v-col cols="auto">
          <v-btn 
            :key="`no${index}`"
            x-large depressed
            :text="values[index]!=-1" 
            :disabled="!job_active"
            :color="$theme.red"
            @click="toggleCheck(index, -1)"
            >
            NO
          </v-btn>
          <v-btn 
            x-large depressed
            :key="`yes${index}`"
            :disabled="!job_active"
            :text="values[index]!=1" 
            :color="$theme.green"
            @click="toggleCheck(index, 1)"
            class="ml-3"
            >
            SI
          </v-btn>
        </v-col>        
      </v-row>
      <v-divider 
        :key="`divider${index}`" 
        v-if="index < step_checks.length -1">
      </v-divider>      
    </template>      
  </v-container>
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
      required: true
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

    values() {
      // const iteration_data = this.$store.state.traceability.current_iteration_data
      // if (iteration_data.procedure) {
      //   const step_id = this.step._id
      //   const step_iteration = iteration_data.procedure.find( step => step._id = step_id)
      //   const value_list = step_iteration.user_data
      //   return value_list
      // }
      // else return []
      return this.$store.getters.getIterationStepUserData(this.step._id)
    },
  },

  methods: {
    toggleCheck(index, check_value) {
      // reset check value to 0 when user clicks a second time on the choice made
      let value = check_value
      if (this.values[index] == check_value) value = 0
      const check_data = {
        step_id: this.step._id,
        value_index: index,
        value
      }
      this.$store.commit('UPDATE_USER_DATA', check_data)
    },
  },

  created() {
    this.step_checks.forEach(() => this.values.push(0))
  }
}
</script>

<style lang="css" scoped>
</style>