<template>
  <v-container fill-height class="px-12 py-8">
    <v-row class="fill-height">

      <!-- AVATAR AND USER UNEDITABLE INFO -->
      <v-col cols="3" class="d-flex flex-column justify-start">
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

        <v-container class="pa-0 mt-12">
          <v-row class="mx-0">
            <v-col cols="6" class="pa-0">
              
              <h5>STATO</h5>
              <v-switch dense hide-details
                :value="user.active">
                <template v-slot:label>
                  <span class="medium">{{user.active ? 'Abilitato' : 'Disabilitato' }}</span>
                </template>
              </v-switch>
              
              <h5 class="mt-8 mb-2">EMAIL</h5>
              <span class="mt-2 medium">{{ user.email || '-' }}</span>
              
              <h5 class="mt-8 mb-2">DIPARTIMENTO</h5>
              <span class="medium">{{ user.department? user.department.name : '-'}}</span>

              <h5 class="mt-8 mb-2">COSTO ORARIO</h5>
              <span class="medium">{{ user.hourly_cost || '-'}}</span>
            </v-col>
            <v-col cols="6" class="pa-0">
              <h5 class="mb-4">PERMESSI</h5>
              <v-checkbox class="mt-2"
                hide-details
                :disabled='!edit_mode'
                v-for="check in permissions" 
                :key="check.name"
                :value="check.name">
                <template v-slot:label>
                  <span class="medium base-white">{{check.label}}</span>
                </template>                
              </v-checkbox>
            </v-col>
          </v-row>
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
      permissions: [
        { name: 'admin', label: 'Amministratore' },
        { name: 'lib:r', label: 'Libreria: sola lettura' },
        { name: 'lib:w', label: 'Libreria: modifica' },
        { name: 'prod:r', label: 'Produzione: sola lettura' },
        { name: 'prod:w', label: 'Produzione: modifica' },
        { name: 'operator', label: 'Operatore'}
      ]
    }
  }
}
</script>

<style lang="css" scoped>
</style>