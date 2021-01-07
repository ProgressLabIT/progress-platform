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
          {{ $tc('user.archive_action') }}
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

          <p>
            {{ $tc('user.archive_explainer') }}
          </p>
          
        </v-row>

        <transition name="slide-fade" mode="out-in">

          <div v-if="stage==='confirm'" key="confirm">
            <v-row justify="space-between" class="mx-0">
              <v-btn :color="$theme.red" @click="archiveUser">
                {{ $tc('confirm') }}
              </v-btn>
              <v-btn :color="$theme.grey" @click="$router.back()">
                {{ $tc('cancel') }}
              </v-btn>
            </v-row>
          </div>

          <div v-else-if="stage==='success'" key="success">
            <v-row no-gutters align="center" class="mx-0">
              <span class="weight-bold highlight">
                {{ $tc('user.archive_success') | capitalize }}
              </span>
              
              <v-spacer></v-spacer>

              <v-btn 
                :color="$theme.grey" 
                @click="$router.push({ name: 'userLibrary' })">
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