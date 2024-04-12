<template>
  <div class="row q-col-gutter-md q-pa-xl">
    <template v-if="user">
      <!-- AVATAR AND USER UNEDITABLE INFO -->
      <div class="col-auto q-pa-md column">
        <q-avatar color="theme-grey" size="140px" class="q-mx-auto q-mb-md">
          <img :src="avatar_src" />
        </q-avatar>

        <template v-if="editMode">
          <q-btn
            v-if="!new_image_url"
            size="12px"
            color="theme-blue"
            icon="mdi-camera"
            :label="$t('edit')"
            @click="$refs.upload_image.click()"
          >
            <input
              ref="upload_image"
              type="file"
              style="display: none"
              accept="image/*"
              @change="updateImg($event.target.files[0])"
            />
          </q-btn>
          <q-btn
            v-else
            size="12px"
            color="theme-orange"
            icon="mdi-restore"
            :label="$t('restore')"
            @click="clearTempImg"
          >
          </q-btn>
        </template>

        <div class="text-h5 uppercase q-mt-lg">
          {{ $t('user.key') }}
        </div>
        <div class="q-mt-xs">
          {{ user_key }}
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
          <template v-if="!editMode">
            <div class="text-h2 uppercase display highlight q-mr-md">
              {{ full_name }}
            </div>

            <q-space />

            <BaseTooltipIcon
              icon="mdi-pencil"
              :tooltip="$capitalize($t('edit'))"
              :color="$theme.blue"
              @icon-click="editMode = true"
            >
            </BaseTooltipIcon>

            <BaseTooltipIcon
              icon="mdi-lock-reset"
              :tooltip="$capitalize($t('user.reset_password'))"
              :color="$theme.orange"
              @icon-click="showPasswordReset"
            >
            </BaseTooltipIcon>

            <BaseTooltipIcon
              icon="mdi-delete"
              :tooltip="$capitalize($t('archive'))"
              :color="$theme.red"
              @icon-click="showDelete"
            >
            </BaseTooltipIcon>
          </template>

          <template v-else>
            <div class="col-3">
              <div class="text-h5 uppercase q-mb-sm">
                {{ $t('user.name') }}
              </div>
              <q-input v-model="temp_data.name" filled dense />
            </div>

            <div class="col-3">
              <div class="text-h5 uppercase q-mb-sm">
                {{ $t('user.surname') }}
              </div>
              <q-input v-model="temp_data.surname" filled dense />
            </div>

            <div class="q-ml-auto">
              <q-btn
                size="12px"
                color="theme-blue"
                class="q-ml-auto"
                :loading="saving"
                :label="$t('save')"
                @click="save"
              >
              </q-btn>
              <q-btn
                size="12px"
                class="q-ml-md"
                color="theme-grey"
                :loading="saving"
                :label="$t('cancel')"
                @click="cancel"
              >
              </q-btn>
            </div>
          </template>
        </div>

        <!-- OTHER DATA -->

        <div class="row q-mt-xl">
          <div class="col-5 column q-gutter-xl">
            <!-- USERNAME -->
            <div>
              <div class="text-h5 uppercase q-mb-sm">
                {{ $t('user.username') }}
              </div>
              <div v-if="!editMode">
                {{ user.username || '-' }}
              </div>
              <q-input v-else v-model="temp_data.username" filled dense>
              </q-input>
            </div>

            <!-- EMAIL -->

            <div>
              <div class="text-h5 uppercase q-mb-sm">
                {{ $t('user.email') }}
              </div>
              <div v-if="!editMode">
                {{ user.email || '-' }}
              </div>
              <q-input v-else v-model="temp_data.email" dense filled> </q-input>
            </div>

            <!-- DEPARTMENT -->
            <div>
              <div class="text-h5 uppercase q-mb-sm">
                {{ $t('user.department') }}
              </div>
              <div v-if="!editMode">
                {{ temp_data.department ? temp_data.department.name : '-' }}
              </div>
              <BaseAutocompleteDepartment
                v-else
                filled
                dense
                :value="temp_data.department"
                @select="updateTempDep"
              >
              </BaseAutocompleteDepartment>
            </div>

            <!-- HOURLY COST -->
            <div>
              <div class="text-h5 uppercase q-mb-sm">
                {{ $t('user.hourly_cost') }}
              </div>
              <div v-if="!editMode">
                {{ $numberFormat(temp_data.hourly_cost || '-', $i18n.locale) }}
              </div>
              <q-input
                v-else
                v-model.number="temp_data.hourly_cost"
                type="number"
                dense
                filled
              >
              </q-input>
            </div>
          </div>

          <div class="col offset-1 column q-gutter-xl">
            <!-- STATUS -->
            <div>
              <div class="text-h5 uppercase">
                {{ $t('user.status_title') }}
              </div>
              <div v-if="!editMode" class="q-mt-sm">
                {{ user_active_text }}
              </div>
              <q-toggle
                v-else
                v-model="temp_data.active"
                filled
                class="q-mt-sm"
                :label="user_active_text"
              >
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
                v-model="user_permissions"
                filled
                dense
                :val="check.name"
                :disable="!editMode"
                class="q-mt-md"
              >
                <span class="high-text">
                  {{ $capitalize($t(`user.permissions.${check.name}`)) }}
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
import { DateTime as DT } from 'luxon';
import BaseAutocompleteDepartment from '@/components/BaseAutocompleteDepartment.vue';
import BaseTooltipIcon from '@/components/BaseTooltipIcon.vue';
import NoDataAlert from '@/components/NoDataAlert.vue';
import scopes_list from '@/lib/UserScopes.js';

export default {
  name: 'UserInfoScreen',

  components: {
    BaseAutocompleteDepartment,
    BaseTooltipIcon,
    NoDataAlert,
  },

  props: {
    user: {
      type: Object,
      required: true,
    },
  },

  data() {
    return {
      editMode: false,
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
      },
    };
  },

  computed: {
    avatar_src() {
      if (!this.user) {
        return '';
      } else if (!this.new_image_url) {
        return (
          this.base_path +
          (this.user.name + this.user.surname).replace(/\s+/g, '') +
          '.jpg'
        ).toLowerCase();
      } else {
        return this.new_image_url;
      }
    },

    full_name() {
      return this.user
        ? this.user.name + ' ' + this.user.surname
        : this.$options.filters.capitalize(this.$t('user.wrong_user_key'));
    },

    user_key() {
      if (this.user) {
        this.setTempData();
      }
      return this.user
        ? this.user._key
        : this.$options.filters.capitalize(this.$t('user.wrong_user_key'));
    },

    user_active_text() {
      const string = this.temp_data.active
        ? this.$t('user.enabled')
        : this.$t('user.disabled');
      return this.$capitalize(string);
    },

    user_permissions: {
      get() {
        return this.temp_data.scope.split(' ');
      },

      set(value) {
        this.temp_data.scope = value.join(' ');
      },
    },
  },

  methods: {
    setTempData() {
      Object.keys(this.temp_data).forEach((key) => {
        this.temp_data[key] = this.user[key];
      });
    },

    formatDate(date_string, with_time) {
      const format = with_time ? DT.DATETIME_MED : DT.DATE_MED;
      return this.$formatDateTime(date_string, this.$i18n.locale, format);
    },

    updateTempDep(department_obj) {
      this.temp_data.department = department_obj;
    },

    updateImg(img) {
      // let url = this.new_image_url
      // if (url) window.URL.revokeObjectURL(url)
      this.new_image_url = window.URL.createObjectURL(img);
      this.new_image = img;
    },

    clearTempImg() {
      window.URL.revokeObjectURL(this.new_image_url);
      this.new_image_url = null;
      this.new_image = null;
    },

    showPasswordReset() {
      this.$router.push({
        name: 'passwordReset',
        params: { user_key: this.user._key },
      });
    },

    showDelete() {
      this.$router.push({
        name: 'userDelete',
        params: { user_key: this.user._key },
      });
    },

    async save() {
      this.saving = true;
      let user_update = {};
      Object.keys(this.temp_data).forEach((k) => {
        if (this.temp_data[k] != this.user[k]) {
          // use only key for department
          if (k === 'department') {
            user_update.department_key = this.temp_data.department._key;
          } else {
            user_update[k] = this.temp_data[k];
          }
        }
      });

      const action_payload = {
        user_key: this.user._key,
        user_update,
        new_image: this.new_image,
      };

      this.$store
        .dispatch('updateUser', action_payload)
        .then(() => {
          this.setTempData();
          this.saving = false;
          this.editMode = false;
        })
        .catch((err) => window.alert(err));
    },

    cancel() {
      this.saving = true;
      this.setTempData();
      this.clearTempImg();
      this.saving = false;
      this.editMode = false;
    },
  },
};
</script>
