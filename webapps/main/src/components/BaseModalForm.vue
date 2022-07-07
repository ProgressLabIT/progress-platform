<template>
  <v-dialog 
    v-model="show"
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
        <v-form @submit="$emit('submit')" lazy-validation v-model="valid">  
          <slot name="form"></slot>
          <v-row class="mt-6">
            <slot name="actions">
              <v-col>
                <v-btn block depressed :color="$theme.blue" @click="$emit('submit')">
                  {{ $tc('save') }}
                </v-btn>
              </v-col>
              <v-col>    
                <v-btn block depressed :color="$theme.grey" @click="$emit('cancel')">
                  {{ $tc('cancel') }}
                </v-btn>
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
    show: {
      type: Boolean,
      default: true
    },
    max_width: {
      type: String,
      default: '500px'
    }
  },

  data () {
    return {
      saving: false,
      valid: true
    }
  },
}
</script>

<style lang="css" scoped>
</style>
