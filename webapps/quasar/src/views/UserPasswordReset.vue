<template>
  <BaseDialog :show="true" :maximized="true" :background="$theme.background">
    <q-card square class="surface1 shadow-12 q-pa-sm" style="max-width: 600px;">
      <q-card-section>
        <div class="text-h3 display highlight">
          {{ $t('user.reset_password') }}
        </div>
      </q-card-section>
      <q-card-section>
        <BaseUserAvatar
          :user="user"
          size="70"
          name_class="solid-white"
          name_style="font-size: 20px">
        </BaseUserAvatar>
      </q-card-section>

      <q-card-section>
        <transition name="slide-fade" mode="out-in">
          <div>
            <div
              v-if="stage==='confirm'"
              key="confirm"
              class="row justify-between">
              <q-btn
                color="theme-red"
                @click="resetPassword"
                :label="$t('confirm')">
              </q-btn>
              <q-btn
                color="theme-grey"
                @click="$router.back()"
                :label="$t('cancel')">
              </q-btn>
            </div>

            <div v-else-if="stage==='show_psw'" key="password">
              <div class="q-mb-xl">
                {{ $t('user.reset_password_success') }}
              </div>

              <div class="text-h5 uppercase">
                {{ $capitalize($t('user.temp_password')) }}
              </div>
              <div class="row justify-between q-mt-sm items-center">
                <div class="col-auto">
                  <div class="background q-pa-sm">
                    <span class="text-h2 highlight">
                      {{ temp_psw }}
                    </span>
                  </div>
                </div>
                <div class="col-auto">
                  <q-btn
                    color="theme-grey"
                    @click="$router.back()"
                    :label="$t('close')">
                  </q-btn>
                </div>
              </div>
            </div>
          </div>

        </transition>
      </q-card-section>
    </q-card>
  </BaseDialog>

</template>

<script>
import BaseDialog from '@/components/BaseDialog.vue'
import BaseUserAvatar from '@/components/BaseUserAvatar.vue'
import { api } from '@/boot/axios.js'
import NonExistentUserGuard from '@/mixins/NonExistentUserGuard.js'

export default {

  name: 'UserPasswordReset',

  mixins: [NonExistentUserGuard],

  components: {
    BaseUserAvatar,
    BaseDialog
  },

  props: {
    user: {
      type: Object
    }
  },

  data() {
    return {
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
