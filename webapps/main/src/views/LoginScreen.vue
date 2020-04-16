<template>
  <v-dialog
    value="true"
    fullscreen no-click-animation persistent
    >

    <v-sheet :color="$theme.black" class="fill">
      <v-container class="fill d-flex align-center"> 
        <v-row justify="center" align="center">
          
          <v-col cols="12" lg="5" class="d-flex justify-end">
            <v-img max-width="300px" src="/media/company/logo.jpg"></v-img>
          </v-col>
          
          <v-divider vertical inset class="mx-4"></v-divider>
          
          <v-col cols="12" lg="6" class="d-flex flex-column justify-center">
            <v-card :color="$theme.background" max-width="500px" class="ml-6">
              
              <!-- <transition name="fade" mode="out-in">  -->
                
                <v-container v-if="!logging_in && !verified" key="form">
                  <v-form @submit="login">
                    <v-card-title class="display">
                        LOGIN
                    </v-card-title>
                    <v-card-text>
                      <v-text-field 
                        v-model="credentials.username" 
                        label="Nome utente"
                        autocomplete="off"/>
                      <v-text-field v-model="credentials.password" type="password" label="Password"/>
                    </v-card-text>
                    <v-card-actions>
                      <v-btn block type="submit" :color="$theme.blue">
                        inizia sessione
                      </v-btn>
                    </v-card-actions>
                  </v-form>
                </v-container>
                
                <v-container key="progress" v-else-if="logging_in">
                  <v-progress-circular 
                    size="80" width="6"
                    indeterminate 
                    :color="$theme.blue"
                    class="mx-auto">
                  </v-progress-circular>
                </v-container>

                <v-container v-else-if="verified" key="success">
                  <BaseUserAvatar 
                    size="90" 
                    :user="user" 
                    :show_name="false"
                    class="ml-3">
                  </BaseUserAvatar>
                    
                  <transition name="slide-fade" mode="out-in"> 
                    <span class="highlight text-uppercase ml-6" :key="user_message">
                      {{ user_message }}
                    </span>
                  </transition>
                </v-container>


                <v-container v-else key="fail"> 
                  Couldn't login. Try again.
                </v-container>

              <!-- </transition> -->

            </v-card>
          </v-col>
        </v-row>
      </v-container>
    </v-sheet>
  </v-dialog>
</template>

<script>
import { api } from '@/lib/apiCall.js'
import BaseUserAvatar from '@/components/BaseUserAvatar.vue'

export default {

  name: 'LoginScreen',

  components: { BaseUserAvatar },

  data () {
    return {
      credentials: {
        username: null,
        password: null,
        // verified: false,
      },
      logging_in: false,
      verified: false,
      user_message: ''
    }
  },

  computed: {
    user() {
      return this.$store.state.session.user
    }
  },

  methods: {
    login() {
      this.logging_in = true

      api.post("/user-session", this.credentials)
        .then( resp => {
          this.$store.commit('START_SESSION', resp.data)
          setTimeout(() => {
            this.logging_in = false
            this.verified = true
            this.user_message = `Benvenuto ${this.user.name} ${ this.user.surname }`
          }, 2000)
          setTimeout(() => {
            this.user_message = "Buon lavoro!"
          }, 4000)
          setTimeout(() => {
            this.$router.push({ name: "productList" })
          }, 6000)
        })
        .catch( err => {
          this.logging_in = false
          this.credentials.username = null
          this.credentials.password = null
          window.alert(err)
        })
    }
  }
}
</script>

<style lang="css" scoped>
</style>