<template>
  <v-dialog
    value="true"
    :overlay-color="$theme.background"
    overlay-opacity="1"
    max-width="600px"
    persistent no-click-animation>

    <v-card>
      <v-card-title>
        <h3 class="display">
          {{ $tc('operations.new_op') }}
        </h3>
      </v-card-title>

      <v-card-text>
        <transition name="slide-fade" mode="out-in">
          <v-form
            @submit.prevent="submit"
            lazy-validation
            v-model="valid"
            v-if="stage==='form'" key="form">
            <v-row>
              <v-col cols="6">
                <h5 class="mt-2 text-uppercase">{{ $tc('name') }}</h5>
                <v-text-field 
                  autocomplete="null"
                  required
                  single-line
                  hide-details
                  v-model="new_operation_data.name"
                  class="pt-0 body-2">
                </v-text-field>
              </v-col>
              <v-col cols="6">
                <h5 class="mt-2 text-uppercase">{{ $tc('code') }}</h5>
                <v-text-field 
                  autocomplete="null"
                  required
                  single-line
                  hide-details
                  v-model="new_operation_data.code"
                  class="pt-0 body-2">
                </v-text-field>
              </v-col>
              <v-col cols="12">
                <h5 class="mt-2 text-uppercase">{{ $tc('description') }}</h5>
                <v-textarea 
                  autocomplete="null"
                  required
                  auto-expand
                  hide-details
                  v-model="new_operation_data.description"
                  class="pt-0 body-2">
                </v-textarea>
              </v-col>
            </v-row>

            <v-row class="mt-6">
              <v-col>
                <v-btn block depressed :color="$theme.blue" @click="submit">salva</v-btn>
              </v-col>
              <v-col>    
                <v-btn block depressed :color="$theme.grey" @click="$router.back()">{{ $tc('cancel') }}</v-btn>
              </v-col> 
            </v-row>  
          </v-form>

          <div v-else-if="stage==='creating'" key="creating">
            <LoadingSignal title=""></LoadingSignal>
          </div>

          <div v-else-if="stage==='success'" key="success">
            <p>{{ $tc('operations.new_op_success') | capitalize }}.</p>

            <v-spacer></v-spacer>

            <v-btn 
              :color="$theme.grey" 
              @click="$router.back()">
              {{ $tc('close') }}
            </v-btn>
          </div>
          
        </transition>


      </v-card-text>
    </v-card>
  </v-dialog>

</template>

<script>
import {capitalize as c} from '@/lib/filters.js'
import LoadingSignal from '@/components/LoadingSignal.vue'

export default {

  name: 'OperationNew',

  components: { LoadingSignal },

  data () {
    return {
      stage: 'form',
      valid: true,
      fields: [
        { title: 'nome', required: true, model: 'name', component: 'v-text-field' },
        { title: 'codice', required: false, model: 'code', component: 'v-text-field' },
        { title: 'descrizione', required: true, model: 'description', component: 'v-textarea' },
      ],
      new_operation_data: {
        name: undefined,
        code: undefined,
        description: undefined
      }
    }
  },

  methods: {
    submit() {
      if (!this.new_operation_data.name) {
        window.alert(c(this.$tc('operations.alerts.op_name_missing')))
      }

      else {
        this.stage = 'creating'
        // this.new_user_data.temp_psw = generateTempPassword(8)
        
        this.$store.dispatch('createOperation', this.new_operation_data)
        .then( () => {
          this.stage = 'success'
        })
        .catch( err => {
          if (err.response.status === 409) {
            window.alert(c(this.$tc('operations.alerts.op_name_used')))
          }
          else { window.alert(err) }
          this.stage = 'form'
        })
      }
    }
  }
}
</script>

<style lang="css" scoped>
</style>