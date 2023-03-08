<template>
  <BaseDialog :show="show" :maximized="true">
    <div class="fixed-full row fit background flex-center">
      <q-card square class="surface1 shadow-12 q-pa-sm" style="max-width: 600px;">
        <q-card-section>
          <div class="text-h3 display highlight">
            {{ $t('user.archive_action') }}
          </div>
        </q-card-section>

        <q-card-section>
          <BaseUserAvatar
            :user="user_data"
            :size="70"
            name_class="solid-white"
            name_style="font-size: 20px">
          </BaseUserAvatar>
          <div class="q-mt-xl">
            {{ $t('user.archive_explainer') }}
          </div>
        </q-card-section>

        <transition name="slide-fade" mode="out-in">
          <q-card-section
            v-if="stage==='confirm'"
            key="confirm"
            align="between">
            <div class="row justify-between">
              <q-btn
                color="theme-red"
                :label="$t('confirm')"
                @click="archiveUser">
              </q-btn>
              <q-btn
                color="theme-grey"
                :label="$t('cancel')"
                @click="$router.back()">
              </q-btn>
            </div>
          </q-card-section>

          <q-card-section
            v-else-if="stage==='success'"
            key="success">
            <div class="row justify-between">
              <div class="weight-bold-highlight">
                {{ $capitalize($t('user.archive_success')) }}
              </div>
              <q-btn
                color="theme-grey"
                :label="$t('close')"
                @click="$router.push({ name: 'userLibrary' })">
              </q-btn>
            </div>
          </q-card-section>
        </transition>
      </q-card>
    </div>
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
    // From route
    user_key: {
      type: String,
    }
  },

  data() {
    return {
      show: true,
      stage: 'confirm',
      temp_psw: ''
    }
  },

  computed: {
    user_data() {
      return this.$store.state.user.user_list.find( user => user._key === this.user_key)
    }
  },
  
  methods:{
    archiveUser() {
      api.delete(`user/${this.user_key}`).then( () => {
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
