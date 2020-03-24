<template>
  <v-dialog 
    value="true"
    :overlay-color="$theme.background"
    overlay-opacity="1"
    :max-width="max_width"
    persistent no-click-animation>
    <v-card>
      
      <v-card-title>  
        <h3 class="display">
          <slot name="title"></slot>
        </h3>
      </v-card-title>

      <v-card-text>
        <v-form @submit="$emit('submit')">  
          <slot name="form"></slot>
          <v-row class="mt-6">
            <slot name="actions">
              <v-col>
                <v-btn block depressed :color="$theme.blue" @click="$emit('submit')">salva</v-btn>
              </v-col>
              <v-col>    
                <v-btn block depressed :color="$theme.grey" @click="$router.back()">annulla</v-btn>
              </v-col> 
            </slot>
          </v-row>  
        </v-form>
      </v-card-text>
    </v-card>
  </v-dialog>
</template>

<script>
export default {

  name: 'BaseModalForm',

  props: {
    max_width: {
      type: String,
      default: '500px'
    }
  },

  data () {
    return {

    }
  },
}
</script>

<style lang="css" scoped>
</style>