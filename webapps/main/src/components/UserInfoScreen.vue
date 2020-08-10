<template>
  <v-container fill-height class="px-12 py-8">
    <v-row class="fill-height">

      <!-- AVATAR AND USER UNEDITABLE INFO -->
      <v-col cols="auto" class="d-flex flex-column">
        <v-avatar 
          :color="$theme.grey" 
          size="140"
          class="mx-auto">
          <v-img :src="avatar_src">
            <!-- <template v-slot:placeholder>
              <v-progress-circular indeterminate></v-progress-circular>
            </template> -->
          </v-img>
        </v-avatar>
        
        <template v-if="edit_mode">
          <div class="mt-4"></div>
          <v-btn small
            v-if="!new_image_url"
            :color="$theme.blue"
            @click="$refs.upload_image.click()">
            <v-icon small>mdi-camera</v-icon>
            <span class="ml-2">
              modifica
            </span>
            <input 
              type="file"
              ref="upload_image"
              style="display: none"
              accept="image/*"
              @change="updateImg($event.target.files[0])" />
          </v-btn>
          <!-- Temporary file uploaded -->
          <v-btn v-else
            small
            :color="$theme.orange"
            @click="clearTempImg">
            <v-icon small>mdi-restore</v-icon>
            <span class="ml-2">
              Ripristina
            </span>
          </v-btn>
        </template>


        <h5 class="mt-6">CODICE UTENTE</h5>
        <span class="body-2">{{ user._key }}</span>

        <h5 class="mt-6">DATA CREAZIONE</h5>
        <span class="body-2">{{ user.created_at | dtFormat(locale, 'dd LLL yyyy') }}</span>

        <h5 class="mt-6">ULTIMO LOGIN</h5>
        <span class="body-2">{{ user.last_login | dtFormat(locale, 'dd LLL yyyy HH:mm') }}</span>

      </v-col>

      <!-- USER EDITABLE INFO -->
      <v-col class="d-flex flex-column fill-height scroll ml-12">

        <v-row class="mx-0 flex-grow-0" align="center">
        
          <template v-if="!edit_mode">
            <h2 
              class="text-uppercase display highlight mr-6">
              {{ full_name }}
            </h2>
            
            <v-spacer></v-spacer>

            <BaseTooltipIcon
              icon="mdi-pencil"
              tooltip="Modifica"
              :color="$theme.blue"
              @iconClick="edit_mode=true">
            </BaseTooltipIcon>

            <BaseTooltipIcon
              icon="mdi-lock-reset"
              tooltip="Reimposta password"
              :color="$theme.orange"
              @iconClick="showPasswordReset">
            </BaseTooltipIcon>

            <BaseTooltipIcon
              icon="mdi-delete"
              tooltip="Archivia"
              :color="$theme.red"
              @iconClick="showDelete">
            </BaseTooltipIcon>            
          
          </template>

          <template v-else>
            <v-col cols="3" class="px-0">
              <h5 class="mb-2">NOME</h5>
              <v-text-field 
                single-line
                hide-details  
                v-model="temp_data.name"
                class="pt-0">
              </v-text-field>
            </v-col>
            <v-col cols="3" offset="1" class="px-0">
              <h5 class="mb-2">COGNOME</h5>
              <v-text-field 
                single-line
                hide-details 
                v-model="temp_data.surname"
                class="pt-0">
              </v-text-field>
            </v-col>

            <v-spacer></v-spacer>
            
            <v-btn small :color="$theme.blue" @click="save" :loading="saving">
              SALVA
            </v-btn>
            <v-btn small :color="$theme.grey" @click="cancel" class="ml-2">
              ANNULLA
            </v-btn>
            
          </template>

        </v-row>


        <v-container class="pa-0 mt-12">
          <v-row class="mx-0">
            <v-col cols="4" class="pa-0">

              <!-- USERNAME -->
              <h5 class="mb-2">NOME UTENTE</h5>
              <span v-if="!edit_mode" class="mt-2 body-2">
                {{ user.username || '-' }}
              </span>
              <v-text-field v-else
                single-line 
                hide-details 
                v-model="temp_data.username"
                class="pt-0">
              </v-text-field>

              <!-- EMAIL -->
              <h5 class="mt-8 mb-2">EMAIL</h5>
              <span v-if="!edit_mode" class="mt-2 body-2">
                {{ user.email || '-' }}
              </span>
              <v-text-field v-else
                single-line 
                hide-details 
                v-model="temp_data.email"
                class="pt-0">
              </v-text-field>


              <!-- DEPARTMENT -->
              <h5 class="mt-8 mb-2">DIPARTIMENTO</h5>
              <span v-if="!edit_mode" class="body-2">{{ temp_data.department ? temp_data.department.name : '-'}}</span>
              <BaseAutocompleteDepartment 
                v-else
                text_classes="body-2"
                :return_object="true"
                :value="temp_data.department"
                @select="updateTempDep($event)"
                :load_departments="false"
                class="pt-0">
              </BaseAutocompleteDepartment>


              <!-- HOURLY COST -->
              <h5 class="mt-8 mb-2">COSTO ORARIO</h5>
              <span v-if="!edit_mode" class="body-2">€ {{ (temp_data.hourly_cost || '-') | numberFormat(locale) }}</span>
              <v-text-field v-else
                type="number"
                single-line 
                hide-details 
                v-model.number="temp_data.hourly_cost"
                prefix="€"
                class="pt-0">
                <template v-slot:></template>
              </v-text-field>

            </v-col>


            <v-col cols="6" offset="2" class="pa-0">

              <!-- STATUS -->
              <h5>STATO</h5>
              <v-switch 
                dense hide-details
                :disabled="!edit_mode"
                v-model="temp_data.active"
                class="mt-2">
                <template v-slot:label>
                  <span class="body-2 base-white">
                    {{ temp_data.active ? 'Abilitato' : 'Disabilitato' }}
                  </span>
                </template>
              </v-switch>

              <!-- SCOPE (PERMISSIONS) -->
              <h5 class="mt-6 mb-4">PERMESSI</h5>
              <v-checkbox class="mt-2"
                hide-details
                multiple
                :disabled='!edit_mode'
                v-for="check in scopes" 
                :key="check.name"
                :value="check.name"
                v-model="user_permissions">
                <template v-slot:label>
                  <span class="body-2 base-white">{{check.label}}</span>
                </template>                
              </v-checkbox>

            </v-col>
          </v-row>
        </v-container>
      </v-col>


    </v-row>

  </v-container>
</template>

<script>
import scopes_list from "@/lib/UserScopes.js"
import BaseAutocompleteDepartment from '@/components/BaseAutocompleteDepartment.vue'
import BaseTooltipIcon from '@/components/BaseTooltipIcon.vue'
import NonExistentUserGuard from '@/mixins/NonExistentUserGuard.js'

export default {

  name: 'UserInfoScreen',

  mixins: [NonExistentUserGuard],

  components: { 
    BaseAutocompleteDepartment,
    BaseTooltipIcon
  },

  props: {
    user: {
      type: Object,
    }
  },

  data () {
    return {
      locale: 'it',
      edit_mode: false,
      saving: false, 
      scopes: scopes_list,
      base_path: '/media/user/',
      new_image_url: null,
      new_image: null,
      show_menu: false,

      temp_data: {
        active: null,
        name: '',
        surname: '',
        username: '',
        email: '', 
        scope: '',
        department: {},
        hourly_cost: 0,
      }
    }
  },

  computed: {
    avatar_src() {
      if (!this.user) {
        return ''
      }

      else if (!this.new_image_url) {
        return this.base_path + (this.user.name + this.user.surname).replace(/\s+/g, '') + '.jpg'
      }

      else return this.new_image_url
    },

    full_name() {
      return this.user ? this.user.name + ' ' + this.user.surname : 'Codice utente errato'
    },

    user_permissions: {
      get() {
        return this.temp_data.scope.split(' ')
      },

      set(value) {
        this.$set(this.temp_data, 'scope', value.join(' ')) 
      }
    }
  },

  methods: {
    setTempData() {
      Object.keys(this.temp_data).forEach( key => {
        this.$set(this.temp_data, key, this.user[key])
      })
    },

    updateTempDep(department_obj) {
      this.$set(this.temp_data, 'department', department_obj)
    },

    updateImg(img) {
      // let url = this.new_image_url
      // if (url) window.URL.revokeObjectURL(url)
      this.new_image_url = window.URL.createObjectURL(img)
      this.new_image = img
    },

    clearTempImg() {
      window.URL.revokeObjectURL(this.new_image_url)
      this.new_image_url = null
      this.new_image = null
    },

    showPasswordReset() {
      this.$router.push({ 
        name: 'passwordReset', 
        params: { user_key: this.user._key }
      })
    },

    showDelete() {
      this.$router.push({
        name: 'userDelete',
        params: { user_key: this.user._key }
      })
    },

    async save() {
      this.saving = true
      let user_update = {}
      Object.keys(this.temp_data).forEach( k => {
        if (this.temp_data[k] != this.user[k]) {
          user_update[k] = this.temp_data[k]
        }
      })

      const action_payload = { 
        user_key: this.user._key, 
        user_update,
        new_image: this.new_image 
      }

      console.log({user_update})
      this.$store.dispatch('updateUser', action_payload)
      .then(() => {
        this.setTempData()
        this.saving = false
        this.edit_mode = false
      })
      .catch( err => window.alert(err) )
    },

    cancel() {
      this.saving = true
      this.setTempData()
      this.clearTempImg()
      this.saving = false
      this.edit_mode = false
    }
  },

  created() {
    this.setTempData()
  }
}
</script>

<style lang="css" scoped>
</style>