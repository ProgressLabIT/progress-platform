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
          {{ $tc('user.new') }}
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
              <v-col 
                cols="6" 
                v-for="field in text_fields" 
                :key="field.model" 
                class="pr-6 pb-0">
                <h5 class="mt-2 text-uppercase">
                  {{ $tc(`user.${field.model}`) }}
                </h5>
                <v-text-field
                  autocomplete="null"
                  :required="field.model === 'username' "
                  single-line 
                  v-model="new_user_data[field.model]"
                  class="pt-0 body-2">
                </v-text-field>
              </v-col>
            
              <v-col cols="6" class="pr-6">
                <h5 class="mt-2 text-uppercase">
                  {{ $tc('department') }}
                </h5>
                <BaseAutocompleteDepartment 
                  text_classes="body-2"
                  @select="new_user_data.department_key = $event"
                  class="pt-0">
                </BaseAutocompleteDepartment>
              </v-col>  

              <v-col cols="6" class="pr-6">
                <h5 class="mt-2 text-uppercase">
                  {{ $tc('user.hourly_cost') }}
                </h5>
                <v-text-field
                  autocomplete="off"
                  type="number"
                  single-line
                  hide-details 
                  v-model.number="new_user_data.hourly_cost"
                  prefix="€"
                  class="pt-0 body-2">
                  <template v-slot:></template>
                </v-text-field>
              </v-col>
            </v-row>

            <h5 class="mt-8 text-uppercase">
              {{ $tc('user.permissions.title') }}
            </h5>
            <v-row>
              <v-col 
                cols="6"
                v-for="check in permissions" 
                :key="check.name" 
                class="py-0">
                <v-checkbox class="mt-2"
                  hide-details
                  multiple
                  :value="check.name"
                  v-model="new_user_data.scopes">
                  <template v-slot:label>
                    <span class="body-2 base-white">{{check.label}}</span>
                  </template>                
                </v-checkbox>
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

          <div v-else-if="stage==='show_psw'" key="password">
            <p>
              {{ $tc('user.new_success') | capitalize }}
            </p>
            
            <h5 class="text-uppercase mt-6 mb-2">
              {{ $tc('user.temp_password')| capitalize }}
            </h5>

            <v-row no-gutters align="center" class="mx-0">
              <v-col cols="auto">
                <v-sheet :color="$theme.background" class="pa-3">
                  <v-row justify="center" align="center" class="mx-0">
                    <h2 class="highlight">{{ temp_psw }}</h2>
                  </v-row>
                </v-sheet>
              </v-col>

              <v-spacer></v-spacer>

              <v-btn 
                :color="$theme.grey" 
                @click="$router.back()">
                {{ $tc('close') }}
              </v-btn>
            </v-row>
          </div>

        </transition>



      </v-card-text>
    </v-card>
  </v-dialog>
</template>

<script>
import user_scopes from "@/lib/UserScopes.js"
import BaseAutocompleteDepartment from '@/components/BaseAutocompleteDepartment.vue'
import LoadingSignal from '@/components/LoadingSignal.vue'
// import generateTempPassword from '@/lib/TokenGenerator.js'

export default {

  name: 'UserNew',

  components: { 
    BaseAutocompleteDepartment,
    LoadingSignal
  },

  data () {
    return {
      text_fields: [
        { model: 'name' },
        { model: 'surname' },
        { model: 'username' },
        { model: 'email' },
      ],
      permissions: user_scopes,
      
      stage: 'form',
      valid: true,
      temp_psw: '',
      
      new_user_data: {
        name: null,
        surname: null,
        username: null,
        email: null,
        department_key: null,
        hourly_cost: null,
        scopes: [], // permissions list
        scope: ''
      }
    }
  },

  watch: {
    'new_user_data.scopes': function(value) {
      this.$set(this.new_user_data, 'scope', value.join(' ')) 
    }
  },

  methods: {
    submit() {
      if (!this.new_user_data.username) {
        window.alert(this.$tc('user.alerts.username_missing'))
      }

      else if (!this.new_user_data.scopes.length) {
        window.alert(this.$tc('user.alerts.permission_missing'))
      }
      
      else {
        this.stage = 'creating'
        // this.new_user_data.temp_psw = generateTempPassword(8)
        
        this.$store.dispatch('createUser', this.new_user_data)
        .then( (temp_psw) => {
          this.stage = 'show_psw'
          this.temp_psw = temp_psw
        })
        .catch( err => {
          if (err.response.status === 409) {
            window.alert(this.$tc('user.alerts.username_already_exists'))
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
