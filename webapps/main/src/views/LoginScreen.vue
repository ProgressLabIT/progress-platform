
<template>
  <v-dialog
    value="true"
    fullscreen no-click-animation persistent
    >

    <v-sheet :color="$theme.black" class="fill">
      <v-container class="fill d-flex align-center">
        <v-row justify="center" align="center">

          <v-col cols="12" md="5" class="d-flex justify-center justify-md-end">
            <v-img max-width="300px" src="/media/progress/progresslab.svg">
              <template v-slot:placeholder>
                <v-avatar size="180" color="primary">
                  <v-col class="text-center highlight">
                    <div>IL</div>
                    <div>VOSTRO</div>
                    <div>LOGO</div>
                  </v-col>
                </v-avatar>
              </template>
            </v-img>
          </v-col>

          <v-divider vertical inset class="mx-4"></v-divider>

          <v-col cols="12" md="5" class="d-flex justify-center justify-md-start px-6">
            <v-card :color="$theme.background" width="100%" max-width="500px">

              <transition name="fade" mode="out-in">

                <v-container v-if="!logging_in && !verified && !reset_password" key="form">
                  <v-form @submit.prevent="login">
                    <v-card-title class="display">
                      {{ $tc('session.login_title') }}
                    </v-card-title>
                    <v-card-text>
                      <v-text-field
                        v-model="credentials.username"
                        :label="$tc('username') | capitalize"
                        autocomplete="off">
                      </v-text-field>

                      <v-text-field
                        v-model="credentials.password"
                        type="password"
                        :label="$tc('user.password') | capitalize">
                      </v-text-field>
                    </v-card-text>
                    <v-card-actions>
                      <v-btn block type="submit" :color="$theme.blue">
                        {{ $tc('session.start_session') }}
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
                  <v-row align="center">

                    <v-col cols="auto" class="ml-5">
                      <BaseUserAvatar
                        size="90"
                        :user="user"
                        :show_name="false">
                      </BaseUserAvatar>
                    </v-col>

                    <v-col>
                      <transition name="slide-fade" mode="out-in">
                        <span class="highlight text-uppercase" :key="user_message">
                          {{ user_message }}
                        </span>
                      </transition>
                    </v-col>

                  </v-row>
                </v-container>


                <v-container v-else-if="reset_password" key="reset_password">
                  <v-form @submit.prevent="resetPassword">
                    <v-card-title class="display">
                      {{ $tc('user.reset_password') }}
                    </v-card-title>

                    <v-card-text>
                      <v-text-field
                        v-model="new_password.first"
                        type="password"
                        :label="$tc('user.new_password') | capitalize"
                        autocomplete="off">
                      </v-text-field>

                      <v-text-field
                        v-model="new_password.second"
                        type="password"
                        label="Password"
                        autocomplete="off">
                      </v-text-field>
                    </v-card-text>

                    <v-card-actions>
                      <v-btn block type="submit" :color="$theme.blue">
                        {{ $tc('user.new_password_save_action') | capitalize }}
                      </v-btn>
                    </v-card-actions>

                  </v-form>
                </v-container>



              </transition>

            </v-card>
          </v-col>
        </v-row>
      </v-container>
    </v-sheet>
  </v-dialog>
</template>

<script>
import { api } from '@/lib/apiCall.js'
import jwt from 'jsonwebtoken'
import BaseUserAvatar from '@/components/BaseUserAvatar.vue'

export default {

  name: 'LoginScreen',

  components: { BaseUserAvatar },

  data () {
    return {
      credentials: {
        username: null,
        password: null,
      },
      user_key: '',
      new_password: {
        first: '',
        second: ''
      },
      logging_in: false,
      verified: false,
      reset_password: false,
      user_message: ''
    }
  },

  computed: {
    user() {
      return this.$store.state.session.user
    },

    go_to_location() {
      const redirect = this.$route.query.redirect_to
      return redirect
        ? { path: redirect }
        : { name: this.$store.getters.userHomepage }
    }
  },

  methods: {
    login() {
      this.logging_in = true

      api.post("auth", this.credentials)
        .then( resp => {
          const token = resp.data.detail.token
          this.$store.commit('UPDATE_AUTH_TOKEN', token)
          this.user_key = jwt.decode(token).sub

          switch (resp.data.detail.action) {
            case 'start_session': {
              this.startSession()
              break
            }

            case 'reset_password': {
              this.reset_password = true
              this.logging_in = false
              break
            }
          }
        })
        .catch( err => {
          this.logging_in = false
          this.credentials.username = null
          this.credentials.password = null
          // if (err.response.status === 409) {
          //   window.alert("Utente attivo su un'altra sessione.")
          // }
          // else {
            window.alert(err)
          // }
        })
    },

    startSession() {
      this.logging_in = true

      api.post(`session`, { user_key: this.user_key })
      .then(resp => {
        this.$store.commit('START_USER_SESSION', resp.data.detail)
        this.$store.dispatch('setSessionTimeout')

        setTimeout(() => {
          this.user_message = this.$tc('session.login_welcome_message_1', 1, {
            name: this.user.name,
            surname: this.user.surname
          })
          this.verified = true
          this.logging_in = false
        }, 1000)
        setTimeout(() => {
          this.user_message = this.$tc('session.login_welcome_message_2')
        }, 3000)
        setTimeout(() => {
          this.$router.push(this.go_to_location)
        }, 5000)
      })
    },

    resetPassword() {
      this.logging_in = true

      api.put(`user/${this.user_key}/password`,
        { new_password: this.new_password.first },
        {
          headers: { 'Content-type': 'application/json' }
        }
      )
      .then( () => {
        this.credentials.password = this.new_password.first
        this.login()
      })
      .catch( err => {
        this.logging_in = false
        this.new_password.first = null
        this.new_password.second = null
        window.alert(err)
      })
    }

  }
}
</script>

<style lang="css" scoped>
</style>
