<template>
  <BaseDialog :show="true" :maximized="true">
    <div class="fixed-full row fit background flex-center">
      <q-card square class="surface1 q-pa-md" style="max-width: 600px">
        <!-- DIALOG TITLE -->
        <q-card-section class="text-h2 display weight-bold">
          {{ $t('user.new') }}
        </q-card-section>

        <transition name="slide-fade" mode="out-in">
          <div v-if="stage === 'form'" key="form">
            <q-card-section>
              <div class="row q-col-gutter-xl text-low">
                <div
                  v-for="field in text_fields"
                  :key="field.model"
                  class="col-6"
                >
                  <div class="text-h5 uppercase">
                    {{ $t(`user.${field.model}`) }}
                  </div>
                  <q-input
                    v-model="new_user_data[field.model]"
                    dense
                    autocomplete="null"
                  >
                  </q-input>
                </div>
                <div class="col-6">
                  <div class="text-h5 uppercase">
                    {{ $t('department') }}
                  </div>
                  <BaseAutocompleteDepartment
                    :value="new_user_data.department_key"
                    key-only
                    @select="new_user_data.department_key = $event"
                  >
                  </BaseAutocompleteDepartment>
                </div>
                <div class="col-6">
                  <div class="text-h5 uppercase">
                    {{ $t('user.hourly_cost') }}
                  </div>
                  <q-input
                    v-model.number="new_user_data.hourly_cost"
                    dense
                    type="number"
                    autocomplete="null"
                  >
                  </q-input>
                </div>
              </div>

              <div class="text-h5 uppercase q-mt-xl text-low">
                {{ $t('user.permissions.title') }}
              </div>
              <div class="row q-col-gutter-x-xl q-col-gutter-y-md q-mt-md">
                <div
                  v-for="check in permissions"
                  :key="check.name"
                  class="col-6"
                >
                  <q-checkbox
                    v-model="new_user_data.scopes"
                    dense
                    :val="check.name"
                  >
                    {{ check.label }}
                  </q-checkbox>
                </div>
              </div>
            </q-card-section>

            <q-card-section>
              <div class="row">
                <div class="col">
                  <q-btn class="full-width" color="theme-blue" @click="submit">
                    {{ $t('save') }}
                  </q-btn>
                </div>
                <div class="col-1"></div>
                <div class="col">
                  <q-btn
                    class="full-width"
                    color="theme-grey"
                    @click="$router.back()"
                  >
                    {{ $t('cancel') }}
                  </q-btn>
                </div>
              </div>
            </q-card-section>
          </div>

          <div v-else-if="stage === 'creating'" key="creating">
            <LoadingSignal />
          </div>

          <div v-else-if="stage === 'show_psw'" key="password">
            <q-card-section>
              {{ $capitalize($t('user.new_success')) }}
            </q-card-section>

            <q-card-section>
              <div class="text-h5 uppercase text-low">
                {{ $capitalize($t('user.temp_password')) }}
              </div>

              <div class="row items-center justify-between q-mt-md">
                <div class="col-auto background q-pa-sm">
                  <div class="text-h2 highlight">
                    {{ temp_psw }}
                  </div>
                </div>

                <q-btn
                  color="theme-grey"
                  :label="$t('close')"
                  @click="$router.back()"
                >
                </q-btn>
              </div>
            </q-card-section>
          </div>
        </transition>
      </q-card>
    </div>
  </BaseDialog>
</template>

<script>
import { storeToRefs } from 'pinia';
import BaseAutocompleteDepartment from '@/components/BaseAutocompleteDepartment.vue';
import BaseDialog from '@/components/BaseDialog.vue';
import LoadingSignal from '@/components/LoadingSignal.vue';
import user_scopes from '@/lib/UserScopes.js';
import { useConfigStore } from '../stores/config';
// import generateTempPassword from '@/lib/TokenGenerator.js'

export default {
  name: 'UserNew',

  components: {
    BaseAutocompleteDepartment,
    BaseDialog,
    LoadingSignal,
  },

  setup() {
    const { config } = storeToRefs(useConfigStore());
    return {
      config,
    };
  },

  data() {
    return {
      text_fields: [
        { model: 'name' },
        { model: 'surname' },
        { model: 'username' },
        { model: 'email' },
      ],
      permissions: user_scopes,

      stage: 'form',
      valid: true,
      temp_psw: '',

      new_user_data: {
        name: null,
        surname: null,
        username: null,
        email: null,
        department_key: null,
        hourly_cost: this.config.operatorCost ?? null,
        scopes: [], // permissions list
        scope: '',
      },
    };
  },

  watch: {
    'new_user_data.scopes': function (value) {
      this.new_user_data.scope = value.join(' ');
    },
  },

  methods: {
    submit() {
      if (!this.new_user_data.username) {
        window.alert(this.$t('user.alerts.username_missing'));
      } else if (!this.new_user_data.scopes.length) {
        window.alert(this.$t('user.alerts.permission_missing'));
      } else {
        this.stage = 'creating';
        // this.new_user_data.temp_psw = generateTempPassword(8)

        this.$store
          .dispatch('createUser', this.new_user_data)
          .then((temp_psw) => {
            this.stage = 'show_psw';
            this.temp_psw = temp_psw;
          })
          .catch((err) => {
            if (err.response.status === 409) {
              window.alert(this.$t('user.alerts.username_already_exists'));
            } else {
              window.alert(err);
            }
            this.stage = 'form';
          });
      }
    },
  },
};
</script>
