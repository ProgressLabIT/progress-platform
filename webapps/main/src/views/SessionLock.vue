<template>
  <v-dialog
    :value="session_locked"
    :overlay-color="$theme.background"
    overlay-opacity="1"
    max-width="600px"
    persistent
    no-click-animation
  >
    <v-card>
      <v-card-title class="text-uppercase">
        {{ $t('session.lock_title') }}
      </v-card-title>

      <v-card-text class="mt-6">
        <!-- <v-col class="pa-0"> -->
        <p>
          <strong>
            {{
              $t('session.lock_salutation', 1, {
                name: user.name,
                surname: user.surname,
              }) | capitalize_all
            }}.
          </strong>
        </p>
        <p>
          {{
            $t('session.lock_explainer', 1, { timeout: session_timeout })
              | capitalize
          }}
        </p>

        <!-- Form is used to allow post via Enter -->
        <v-form @submit.prevent="verifyUser">
          <v-text-field
            v-model="password"
            :label="$t('user.password') | capitalize"
            type="password"
            single-line
          >
          </v-text-field>

          <v-row class="mx-0 mt-6" justify="space-between">
            <v-btn
              large
              type="submit"
              :color="$theme.blue"
              :loading="reloading_session"
            >
              {{ $t('resume') }}
            </v-btn>
            <v-btn large :color="$theme.grey" @click="logout">
              {{ $t('session.close_session') }}
            </v-btn>
          </v-row>
        </v-form>
        <!-- </v-col> -->
      </v-card-text>
    </v-card>
  </v-dialog>
</template>

<script>
import { capitalize as c } from '@/lib/filters.js';
import { api } from '@/lib/apiCall';

export default {
  name: 'SessionLock',

  props: {
    session_locked: Boolean,
  },

  data() {
    return {
      password: '',
      reloading_session: false,
    };
  },

  computed: {
    user() {
      return this.$store.state.session.user;
    },

    session_timeout() {
      return this.$store.state.session.session_timeout;
    },
  },

  methods: {
    verifyUser() {
      this.reloading_session = true;
      api
        .post(`/user/${this.user._key}/verify`, { password: this.password })
        .then(() => {
          this.$store.dispatch('unlockSession');
        });
    },

    async logout() {
      const confirm = window.confirm(c(this.$t('session.alerts.close_alert')));
      if (confirm) {
        await this.$store.dispatch('logout');
      }
    },
  },
};
</script>

<style lang="css" scoped></style>
