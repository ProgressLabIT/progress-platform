<template>
  <v-dialog 
    v-model="showModal"
    :overlay-color="$theme.background"
    overlay-opacity="1"
    max-width="600px"
    persistent no-click-animation>
    <v-card>
      
      <v-card-title>  
        <h3 class="display">
          {{ $tc('operation.delete_title') | capitalize }}
        </h3>
      </v-card-title>

      <v-card-text>

        <transition name="slide-fade" mode="out-in">

          <div v-if="stage==='confirm'" key="confirm">

            <div class="my-4">
              <p>{{ $tc('operation_delete.question') | capitalize }}?</p> 
              <h3 class="mb-12 text-uppercase weight-bold">
                {{ operation.name }} 
              </h3>
            </div>
            <v-row justify="space-between" class="mx-0">
              <v-btn :color="$theme.red" @click="deleteOperation">
                {{ $tc('confirm') }}
              </v-btn>
              <v-btn :color="$theme.grey" @click="$router.back()">
                {{ $tc('cancel') }}
              </v-btn>
            </v-row>
          </div>

          <div v-else-if="stage==='success'" key="success">
            <v-row no-gutters align="center" class="mx-0">
              <span class="weight-bold highlight">
                {{ $tc('operation.delete_success') | capitalize }}.
              </span>
              
              <v-spacer></v-spacer>

              <v-btn 
                :color="$theme.grey" 
                @click="$router.push({ name: 'operationLibrary' })">
                CHIUDI
              </v-btn>
            </v-row>
          </div>

        </transition>

      </v-card-text>
    </v-card>
  </v-dialog>
</template>

<script>
import { api } from '@/lib/apiCall.js'
import NonExistentOperationGuard from "@/mixins/NonExistentOperationGuard.js"

export default {

  name: 'OperationDelete',

  mixins: [NonExistentOperationGuard],

  props: {
    operation: {
      type: Object
    }
  },

  data () {
    return {
      showModal: true,
      stage: 'confirm',
    }
  },

  methods:{
    deleteOperation() {
      api.delete(`operation/${this.operation._key}`)
      .then( async () => {
        // reload users from backend to make sure archived user is not present
        await this.$store.dispatch('getOperations')
        this.stage = 'success' 
      })
      .catch(err => {
        // Operation is in use in some process    
        if (err.response.status === 403) {
          const error_message = this.$tc('operation.alerts.op_in_use') + ": "
          window.alert(error_message + err.response.data.detail.product_codes)
          this.$router.back()
        }
        else {
          window.alert(this.$tc('operation.alerts.delete_general_error'))
        }
      })
    }
  },
}
</script>

<style lang="css" scoped>
</style>