<template>
  <div>
    <h5 class="mb-2">FOTO</h5>
    <v-row class="ml-n1">
      <v-col class="pa-1" cols="3" v-for="pic in 3" :key="pic">
        <v-card outlined>
          <v-img src="http://source.unsplash.com/300x200?product"/>
        </v-card>
      </v-col>  
      <v-col v-if="edit_mode" cols="3" class="align-self-center text-center">
        <v-icon :color="$theme.whitelow">add_a_photo</v-icon>              
        <p class="smaller text-uppercase mt-2">Aggiungi immagini</p>
      </v-col>  
    </v-row>  
  </div>
</template>

<script>
// import { mapState } from 'vuex'
export default {

  name: 'StepInstruction',

  props: ['phase_no', 'step_no', 'edit_mode'],

  computed: {

    pic_no() {
      const rand = Math.random()*5
      return Math.ceil(rand)
    },
  }
};
</script>

<style lang="css" scoped>
</style>
