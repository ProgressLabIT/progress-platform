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
          Archivia Utente
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

          <!-- <p>I dati dell'utente verranno effettivamente eliminati SOLO nel caso in cui non ci siano eventi di tracciabilità associati ad esso. In questo caso l'utente verrà semplicemente archiviato: non verrà visualizzato nell'elenco degli utenti, ma potrà essere ripristinato dalla sezione archivio e i suoi dati saranno visibili in caso di analisi dello storico.</p> -->
          <p>I dati dell'utente non verranno effettivamente eliminati ma solo archiviati: l'utente non verrà visualizzato negli elenchi, ma potrà essere ripristinato dalla sezione archivio e i suoi dati saranno visibili in caso di analisi dello storico.</p>
          
        </v-row>

        <transition name="slide-fade" mode="out-in">

          <div v-if="stage==='confirm'" key="confirm">
            <v-row justify="space-between" class="mx-0">
              <v-btn :color="$theme.red" @click="archiveUser">
                CONFERMA
              </v-btn>
              <v-btn :color="$theme.grey" @click="$router.back()">
                ANNULLA
              </v-btn>
            </v-row>
          </div>

          <div v-else-if="stage==='success'" key="success">
            <v-row no-gutters align="center" class="mx-0">
              <span class="weight-bold highlight">Utente archiviato con successo.</span>
              
              <v-spacer></v-spacer>

              <v-btn 
                :color="$theme.grey" 
                @click="$router.push({ name: 'userLibrary' })">
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
      type: Object,
    }
  },

  data() {
    return {
      showModal: true,
      stage: 'confirm',
      temp_psw: ''
    }
  },

  
  methods:{
    archiveUser() {
      api.delete(`user/${this.user._key}`).then( () => {
        // reload users from backend to make sure archived user is not present
        this.$store.dispatch('loadUsers')
        this.stage = 'success' 
      })
    }
  },
}
</script>

<style lang="css" scoped>
</style>