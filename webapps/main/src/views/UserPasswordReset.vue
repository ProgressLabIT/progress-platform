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
          reimposta password
        </h3>
      </v-card-title>

      <v-card-text>

        <v-row class="mx-0">
          <BaseUserAvatar 
            :user="user"
            :size="70"
            name_class="solid-white"
            name_style="font-size: 20px"
            class="my-8">
          </BaseUserAvatar>
        </v-row>

        <transition name="slide-fade" mode="out-in">

          <div v-if="stage==='confirm'" key="confirm">
            <v-row justify="space-between" class="mx-0">
              <v-btn :color="$theme.red" @click="resetPassword">
                CONFERMA
              </v-btn>
              <v-btn :color="$theme.grey" @click="$router.back()">
                ANNULLA
              </v-btn>
            </v-row>
          </div>

          <div v-else-if="stage==='show_psw'" key="password">
            <p>Password reimpostata con successo. Prendi nota della password temporanea per l'utente. Non verrà mostrata di nuovo. Al prossimo accesso l'utente dovrà sostituirla con una privata.</p>
            
            <h5 class="text-uppercase mt-6 mb-2">Password temporanea</h5>
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
import BaseUserAvatar from '@/components/BaseUserAvatar.vue'
import { api } from '@/lib/apiCall.js'
import NonExistentUserGuard from '@/mixins/NonExistentUserGuard.js'



export default {

  name: 'UserPasswordReset',

  mixins: [NonExistentUserGuard],

  components: { 
    BaseUserAvatar,
  },

  props: {
    user: {
      type: Object
    }
    // user_key: {
    //   type: String,
    //   required: true
    // }
  },

  data() {
    return {
      showModal: true,
      stage: 'confirm',
      temp_psw: ''
    }
  },

  // computed: {
  //   user_data() {
  //     return this.$store.state.user.user_list.find( user => user._key === this.user_key)
  //   }
  // },

  methods:{
    resetPassword() {
      api.delete(`user/${this.user._key}/password`).then( resp => {
        this.temp_psw = resp.data.detail.temp_psw
        this.stage = 'show_psw'
      })
    }
  }
}
</script>

<style lang="css" scoped>
</style>