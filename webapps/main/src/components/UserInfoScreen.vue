<template>
  <div class="row q-col-gutter-md q-pa-xl">
    <template v-if="user">
      <!-- AVATAR AND USER UNEDITABLE INFO -->
      <div class="col-auto q-pa-md column">
        <q-avatar
          color="theme-grey"
          size="140px"
          class="q-mx-auto q-mb-md">
          <img :src="avatar_src" />
        </q-avatar>

        <template v-if="edit_mode">
          <q-btn
            v-if="!new_image_url"
            size="12px"
            color="theme-blue"
            @click="$refs.upload_image.click()"
            icon="mdi-camera"
            :label="$t('edit')">
            <input
              type="file"
              ref="upload_image"
              style="display: none"
              accept="image/*"
              @change="updateImg($event.target.files[0])" />
          </q-btn>
          <q-btn
            v-else
            size="12px"
            color="theme-orange"
            @click="clearTempImg"
            icon="mdi-restore"
            :label="$t('restore')">
          </q-btn>
        </template>

        <div class="text-h5 uppercase q-mt-lg">
          {{ $t('user.key') }}
        </div>
        <div class="q-mt-xs">
          {{ user._key }}
        </div>

        <div class="text-h5 uppercase q-mt-lg">
          {{ $t('user.creation_date') }}
        </div>
        <div class="q-mt-xs">
          {{ formatDate(user.created_at) }}
        </div>

        <div class="text-h5 uppercase q-mt-lg">
          {{ $t('user.last_login') }}
        </div>
        <div class="q-mt-xs">
          {{ formatDate(user.last_login, true) }}
        </div>
      </div>

      <!-- USER EDITABLE INFO -->
      <div class="col q-pl-xl">

        <!-- NAME AND SURNAME -->
        <div class="row q-gutter-xl items-center">
          <template v-if="!edit_mode">
            <div class="text-h2 uppercase display highlight q-mr-md">
              {{ full_name}}
            </div>

            <q-space />

            <BaseTooltipIcon
              icon="mdi-pencil"
              :tooltip="$capitalize($t('edit'))"
              :color="$theme.blue"
              @iconClick="edit_mode=true">
            </BaseTooltipIcon>

            <BaseTooltipIcon
              icon="mdi-lock-reset"
              :tooltip="$capitalize($t('user.reset_password'))"
              :color="$theme.orange"
              @iconClick="showPasswordReset">
            </BaseTooltipIcon>

            <BaseTooltipIcon
              icon="mdi-delete"
              :tooltip="$capitalize($t('archive'))"
              :color="$theme.red"
              @iconClick="showDelete">
            </BaseTooltipIcon>
          </template>

          <template v-else>
            <div class="col-3">
              <div class="text-h5 uppercase">
                {{ $t('user.name') }}
              </div>
              <q-input dense v-model="temp_data.name" />
            </div>

            <div class="col-3">
              <div class="text-h5 uppercase">
                {{ $t('user.surname') }}
              </div>
              <q-input dense v-model="temp_data.surname" />
            </div>

            <div class="q-ml-auto">
              <q-btn
                size="12px"
                color="theme-blue"
                class="q-ml-auto"
                @click="save"
                :loading="saving"
                :label="$t('save')">
              </q-btn>
              <q-btn
                size="12px"
                class="q-ml-md"
                color="theme-grey"
                @click="cancel"
                :loading="saving"
                :label="$t('cancel')">
              </q-btn>
            </div>
          </template>
        </div>

        <!-- OTHER DATA -->

        <div class="row q-mt-xl">
          <div class="col-4 column q-gutter-xl">

            <!-- USERNAME -->
            <div>
              <div class="text-h5 uppercase">
                {{ $t('user.username') }}
              </div>
              <div v-if="!edit_mode" class="q-mt-sm">
                {{ user.username || '-' }}
              </div>
              <q-input
                dense
                v-else
                v-model="temp_data.username">
              </q-input>
            </div>

            <!-- EMAIL -->

            <div>
              <div class="text-h5 uppercase">
                {{ $t('user.email') }}
              </div>
              <div v-if="!edit_mode" class="q-mt-sm">
                {{ user.email || '-' }}
              </div>
              <q-input
                dense
                v-else
                v-model="temp_data.email">
              </q-input>
            </div>

            <!-- DEPARTMENT -->
            <div>
              <div class="text-h5 uppercase">
                {{ $t('user.department') }}
              </div>
              <div v-if="!edit_mode" class="q-mt-sm">
                {{ temp_data.department ? temp_data.department.name : '-'}}
              </div>
              <BaseAutocompleteDepartment
                v-else
                :value="temp_data.department"
                @select="updateTempDep">
              </BaseAutocompleteDepartment>
            </div>

            <!-- HOURLY COST -->
            <div>
              <div class="text-h5 uppercase">
                {{ $t('user.hourly_cost') }}
              </div>
              <div v-if="!edit_mode" class="q-mt-sm">
                {{ $numberFormat((temp_data.hourly_cost || '-'), locale) }}
              </div>
              <q-input
                v-else
                type="number"
                dense
                v-model.number="temp_data.hourly_cost">
              </q-input>
            </div>

          </div>


          <div class="col-4 offset-2 column q-gutter-xl">

            <!-- STATUS -->
            <div>
              <div class="text-h5 uppercase">
                {{ $t('user.status_title') }}
              </div>
              <div v-if="!edit_mode" class="q-mt-sm">
                {{ user_active_text }}
              </div>
              <q-toggle
                v-else
                dense
                class="q-mt-sm"
                v-model="temp_data.active"
                :label="user_active_text">
              </q-toggle>
            </div>

            <!-- SCOPE (PERMISSIONS) -->
            <div class="column">
              <div class="text-h5 uppercase">
                {{ $t('user.permissions.title') }}
              </div>
              <q-checkbox
                v-for="check in scopes"
                :key="check.name"
                dense
                :val="check.name"
                :disable="!edit_mode"
                v-model="user_permissions"
                class="q-mt-md">
                <span class="high-text">
                  {{ $capitalize($t(`user.permissions.${check.name}`))}}
                </span>
              </q-checkbox>
            </div>
          </div>
        </div>


      </div>
    </template>
    <NoDataAlert v-else />

  </div>
</template>

<script>
import scopes_list from "@/lib/UserScopes.js"
import NoDataAlert from '@/components/NoDataAlert.vue'
import BaseAutocompleteDepartment from '@/components/BaseAutocompleteDepartment.vue'
import BaseTooltipIcon from '@/components/BaseTooltipIcon.vue'
import { DateTime as DT } from 'luxon'

export default {

  name: 'UserInfoScreen',

  components: {
    BaseAutocompleteDepartment,
    BaseTooltipIcon,
    NoDataAlert
  },

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
        return (this.base_path + (this.user.name + this.user.surname).replace(/\s+/g, '') + '.jpg').toLowerCase()
      }

      else return this.new_image_url
    },

    full_name() {
      return this.user
        ? this.user.name + ' ' + this.user.surname
        : this.$options.filters.capitalize(this.$t('user.wrong_user_key'))
    },

    user_active_text() {
      const string = this.temp_data.active
        ? this.$t('user.enabled')
        : this.$t('user.disabled')
      return this.$capitalize(string)
    },

    user_permissions: {
      get() {
        return this.temp_data.scope.split(' ')
      },

      set(value) {
        this.temp_data.scope = value.join(' ')
      }
    }
  },

  methods: {
    setTempData() {
      Object.keys(this.temp_data).forEach( key => {
        this.temp_data[key] = this.user[key]
      })
    },

    formatDate(date_string, with_time) {
      const format = with_time ? DT.DATETIME_MED : DT.DATE_MED
      return this.$formatDateTime(date_string, this.$i18n.locale, format)
    },

    updateTempDep(department_obj) {
      this.temp_data.department = department_obj
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
          // use only key for department
          if (k === 'department') {
            user_update.department_key = this.temp_data.department._key
          }
          else {
            user_update[k] = this.temp_data[k]
          }
        }
      })

      const action_payload = {
        user_key: this.user._key,
        user_update,
        new_image: this.new_image
      }

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
    if (this.user) {
      this.setTempData()
    }
  }
}
</script>

<style lang="css" scoped>
</style>
