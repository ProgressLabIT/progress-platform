<template>
  <v-container fluid class="scroll pt-12 px-12" :style="'max-height:'+height+'px'">
          
    <template v-for="(check, index) in step_checks" >
      <v-row 
        :key="index"
        align="top">
        <v-col cols="1" class="d-flex align-center">
          <v-avatar 
            :color="values[index]!=0 ? $theme.blue : 'transparent'" 
            size="24" 
            class="d-flex text-center body-2 font-weight-medium">
            <span :class="values[index]!=0 ? 'solid-white weight-bold': ''">
            {{ index + 1 }}
            </span>
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
            :color="$theme.red"
            @click="toggleCheck(index, -1)"
            >
            NO
          </v-btn>
          <v-btn 
            x-large depressed
            :key="`yes${index}`"
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
        :key="index" 
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
      current_check: 0,
      values: []
    }
  },

  computed: {
    step_checks() {
      return this.step.checks
    },
  },

  methods: {
    toggleCheck(index, value) {
      if (this.values[index] == value) this.$set(this.values, index, 0) 
      else this.$set(this.values, index, value)
    },
  },

  created() {
    this.step_checks.forEach(() => this.values.push(0))
  }
}
</script>

<style lang="css" scoped>
</style>