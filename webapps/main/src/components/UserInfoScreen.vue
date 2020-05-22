<template>
  <v-container fill-height class="px-12 py-8">
    <v-row class="fill-height">

      <!-- AVATAR AND USER UNEDITABLE INFO -->
      <v-col cols="4" class="d-flex flex-column justify-start">
        <BaseUserAvatar 
          :user="user"
          size="140" 
          :show_name="false"
          class="flex-grow-0">
        </BaseUserAvatar>

        <v-spacer></v-spacer>

        <h5 class="mt-6">CODICE UTENTE</h5>
        <span class="body-2">{{ user._key }}</span>

        <h5 class="mt-6">DATA CREAZIONE</h5>
        <span class="body-2">{{ user.created_at | dtFormat(locale, 'dd LLL yyyy') }}</span>

        <h5 class="mt-6">ULTIMO LOGIN</h5>
        <span class="body-2">{{ user.last_login | dtFormat(locale, 'dd LLL yyyy HH:mm') }}</span>

        <!-- <v-row v-for="(value, key) in user" :key="key">
          {{ key }}: {{ value }}
        </v-row>       -->
      </v-col>

      <!-- USER EDITABLE INFO -->
      <v-col >
        <h2 
          v-if="!edit_mode"
          class="text-uppercase display highlight mt-6">
          {{ user.name }} {{ user.surname }}
        </h2>

        <v-container>
        </v-container>
      </v-col>


    </v-row>

    <!-- EDIT BUTTON -->
    <v-btn 
      fixed fab bottom right 
      class="mb-12 mr-2" 
      :color="$theme.blue">
      <v-icon>mdi-pencil</v-icon>
    </v-btn>
  </v-container>
</template>

<script>
import BaseUserAvatar from '@/components/BaseUserAvatar.vue'

export default {

  name: 'UserInfoScreen',

  components: { BaseUserAvatar },

  props: {
    user: {
      type: Object,
      required: true
    }
  },

  data () {
    return {
      locale: 'it',
      edit_mode: false,
    }
  }
}
</script>

<style lang="css" scoped>
</style>