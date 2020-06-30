<template>
  <v-dialog
    :value="session_locked"
    :overlay-color="$theme.background"
    overlay-opacity="1"
    max-width="600px"
    persistent no-click-animation>
    <v-card>
      <v-card-title>
        SESSIONE IN PAUSA
      </v-card-title>

      <v-card-text class="mt-6">
        <!-- <v-col class="pa-0"> -->
          <p><strong>Ciao {{ user.name }} {{ user.surname }}.</strong></p>
          <p>La sessione è stata sospesa per la tua sicurezza o perché inattiva per più di {{ session_timeout }} minuti o a causa di un ricaricamento della pagina. Inserisci la password per riprendere la sessione. Se vuoi cambiare utente, chiudi e inizia una nuova sessione.</p>
          <v-form @submit.prevent="verifyUser">
            <v-text-field
              v-model="password"
              label="Password"
              type="password"
              single-line>
            </v-text-field>

            <v-row class="mx-0 mt-6" justify="space-between">
              <v-btn 
                large 
                type="submit"
                :color="$theme.blue" 
                :loading="reloading_session">
                Riprendi
              </v-btn>
              <v-btn large :color="$theme.grey" @click="logout">
                Chiudi sessione
              </v-btn>
            </v-row>
          </v-form>
        <!-- </v-col> -->
      </v-card-text>
    </v-card>
  </v-dialog>
</template>

<script>
import { api } from '@/lib/apiCall'

export default {

  name: 'SessionLock',

  props: {
    session_locked: Boolean
  },

  data () {
    return {
      password: '',
      reloading_session: false
    }
  },

  computed: {
    user() {
      return this.$store.state.session.user
    },

    session_timeout() {
      return this.$store.state.session.session_timeout
    },
  },

  methods: {
    verifyUser() {
      this.reloading_session = true
      api.post(`/user/${this.user._key}/verify`, { password: this.password })
      .then( () => {
        this.$store.dispatch('unlockSession')
      })
    },

    async logout() {
      const confirm = window.confirm('Sicuro di voler terminare la sessione?')
      if (confirm) {
        await this.$store.dispatch('logout')
      }
    }
  }
}
</script>

<style lang="css" scoped>
</style>