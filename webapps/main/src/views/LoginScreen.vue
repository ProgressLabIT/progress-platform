
<template>
  <div class="fullscreen background flex flex-center">
    <div class="row full-width items-center">
      <div class="row col-5 justify-end">
      <q-img width="300px" height="300px" src="/progresslab.svg">
        <template v-slot:error>
          <q-avatar size="180" color="blue">
            <div class="column text-center highlight">
              <div>IL</div>
              <div>VOSTRO</div>
              <div>LOGO</div>
            </div>
          </q-avatar>
        </template>
      </q-img>
      </div>

      <q-separator vertical class="q-mx-xl"/>

      <q-card
        class="surface1 full-height col-3 q-pa-lg"
        square
        style="width:500px">
        <transition name="fade" mode="out-in">

          <!-- LOGIN FORM -->
          <q-form
            v-if="!logging_in && !verified && !reset_password"
            key="form"
            @submit.prevent="login">
            <q-card-section>
              <div class="card-title text-high">
                {{ $t('session.login_title') }}
              </div>
            </q-card-section>

            <q-card-section>
              <q-input
                v-model="credentials.username"
                :label="$capitalize($t('user.username'))"
                autocomplete="off"
                class="q-mb-md">
              </q-input>
              <q-input
                v-model="credentials.password"
                type="password"
                :label="$capitalize($t('user.password'))">
              </q-input>
            </q-card-section>

            <q-card-actions>
              <q-btn type="submit" color="theme-blue" class="full-width">
                {{ $t('session.start_session') }}
              </q-btn>
            </q-card-actions>
          </q-form>

          <div key="progress" v-else-if="logging_in">
            <q-spinner
              size="80px" :thickness="4"
              indeterminate
              color="theme-blue"
              class="q-ma-xl">
            </q-spinner>
          </div>

          <!-- WELCOME MESSAGE -->
          <div v-else-if="verified" key="success">
            <div class="row items-center">

              <div class="col-auto q-ml-md">
                <BaseUserAvatar
                  size="90px"
                  :user="user"
                  :show_name="false">
                </BaseUserAvatar>
              </div>

              <div class="col q-ml-md">
                <transition name="slide-fade" mode="out-in">
                  <span class="highlight text-uppercase" :key="user_message">
                    {{ user_message }}
                  </span>
                </transition>
              </div>

            </div>
          </div>


          <!-- RESET PASSWORD -->
          <div v-else-if="reset_password" key="reset_password">
            <q-form @submit.prevent="resetPassword">
              <q-card-section>
                <div class="card-title text-high">
                {{ $t('user.reset_password') }}
                </div>
              </q-card-section>

              <q-card-section>
                <q-input
                  v-model="new_password.first"
                  type="password"
                  :label="$capitalize($t('user.new_password'))"
                  autocomplete="off">
                </q-input>

                <q-input
                  v-model="new_password.second"
                  type="password"
                  label="Password"
                  autocomplete="off">
                </q-input>
              </q-card-section>

              <q-card-actions>
                <q-btn
                  type="submit"
                  color="theme-blue"
                  class="full-width"
                  :disabled="!password_match">
                  {{ $capitalize($t('user.new_password_save_action')) }}
                </q-btn>
              </q-card-actions>

            </q-form>
          </div>


        </transition>
      </q-card>

    </div>
  </div>
</template>

<script>
import { api } from 'boot/axios.js'
import jwt_decode from 'jwt-decode'
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
    },

    password_match() {
      let can_reset = this.reset_password
        && this.new_password.first.length > 0
        && this.new_password.first === this.new_password.second

      return can_reset
    }
  },

  methods: {
    login() {
      this.logging_in = true

      api.post("auth", this.credentials)
        .then( resp => {
          const token = resp.data.detail.token
          this.$store.commit('UPDATE_AUTH_TOKEN', token)
          this.user_key = jwt_decode(token).sub

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
        this.$store.commit('SET_SESSION_TIMEOUT')

        setTimeout(() => {
          this.user_message = this.$t('session.login_welcome_message_1', {
            name: this.user.name,
            surname: this.user.surname
          })
          this.verified = true
          this.logging_in = false
        }, 1000)
        setTimeout(() => {
          this.user_message = this.$t('session.login_welcome_message_2')
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
