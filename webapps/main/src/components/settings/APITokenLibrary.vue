<template>
  <LoadingSignal v-if="!data_ready" />

  <div v-else class="row full-height">
    <div class="full-height column col">
      <div
        class="row q-mt-md q-px-lg q-py-sm text-h6 text-uppercase weight-bold"
      >
        <div class="col-3">
          {{ $t('expiration') }}
        </div>
        <div class="col-3">
          {{ $t('description') }}
        </div>
        <div class="col-4">
          {{ $t('signature') }}
        </div>
      </div>

      <q-separator />

      <!-- TOKEN LIST -->
      <div class="scroll col">
        <div
          v-for="(tk, index) in token_list"
          :key="tk._key"
          :dense="dense"
          :readonly="!editMode"
          class="row pointer q-px-lg q-py-xs medium full-width"
          :class="{
            'alternate-row': index % 2 === 0,
            'bg-blue-backdrop': tk._key === selected_token_key,
          }"
          style="white-space: nowrap"
          @click="selectToken(tk._key)"
        >
          <div class="col-3">
            {{ $capitalize(formatDate(tk.expires_at)) }}
          </div>
          <div class="col-3">
            {{ $capitalize(tk.description) }}
          </div>
          <div class="col-4">
            {{ $capitalize(tk.signature) }}
          </div>
        </div>
      </div>

      <q-separator />

      <!-- TOKEN LIST COUNT -->
      <div class="row flex-center smaller q-py-xs">
        {{ token_list.length }}
      </div>

      <div class="row q-pa-md justify-between">
        <q-btn
          v-if="editMode"
          color="theme-blue"
          class="col-auto"
          size="12px"
          :label="$t('api_token_add')"
          @click="show_new_api_token_form = true"
        >
        </q-btn>
        <q-btn
          v-if="selected_token_key && editMode"
          color="theme-red"
          class="col-auto"
          size="12px"
          :label="$t('api_token_delete')"
          :readonly="!editMode"
          @click="show_delete = true"
        >
        </q-btn>
      </div>
    </div>

    <BaseDialog
      :show="show_new_api_token_form"
      :no-backdrop-dismiss="false"
      @close="closeAddTokenForm"
    >
      <BaseActionCard
        :title="$t('api_token_add')"
        :save-label="$t('confirm')"
        @save="createToken"
        @cancel="closeAddTokenForm"
      >
        <q-form ref="token-form">
          <q-card-section>
            {{ $t('api_token_add_text') }}
          </q-card-section>
          <q-card-section>
            <q-input
              v-model="token_description"
              dense
              filled
              hide-bottom-space
              :label="$t('description')"
            />
          </q-card-section>
          <q-card-section>
            <q-input
              v-model="token_expiry_date"
              dense
              filled
              mask="####-##-##"
              hide-bottom-space
              :rules="[checkDate]"
              :label="$t('expiration')"
            >
              <template #append>
                <q-icon name="mdi-calendar" class="cursor-pointer">
                  <q-popup-proxy
                    cover
                    transition-show="scale"
                    transition-hide="scale"
                  >
                    <q-date
                      v-model="token_expiry_date"
                      minimal
                      mask="YYYY-MM-DD"
                    >
                      <div class="row items-center justify-end">
                        <q-btn
                          v-close-popup
                          label="Close"
                          color="primary"
                          flat
                        />
                      </div>
                    </q-date>
                  </q-popup-proxy>
                </q-icon>
              </template>
            </q-input>
          </q-card-section>
        </q-form>
      </BaseActionCard>
    </BaseDialog>

    <BaseDialog
      :show="show_new_api_token"
      :no-backdrop-dismiss="false"
      @close="show_new_api_token = false"
    >
      <BaseActionCard
        :title="$t('api_token_add')"
        :save-label="$t('copy_to_clipboard')"
        :cancel-label="$t('confirm')"
        @save="onClipboard"
        @cancel="show_new_api_token = false"
      >
        <q-input v-model="token" filled type="textarea" />
      </BaseActionCard>
    </BaseDialog>

    <BaseDialog
      :show="show_delete"
      :no-backdrop-dismiss="false"
      @close="show_delete = false"
    >
      <BaseActionCard
        :title="$t('api_token_delete')"
        :save-label="$t('confirm')"
        save-color="theme-red"
        @save="deleteToken"
        @cancel="show_delete = false"
      >
        {{ $t('api_token_delete_text') }}
      </BaseActionCard>
    </BaseDialog>
  </div>
</template>

<script>
import { DateTime as DT } from 'luxon';
import { copyToClipboard, date } from 'quasar';
import BaseActionCard from '@/components/BaseActionCard.vue';
import BaseDialog from '@/components/BaseDialog.vue';
import LoadingSignal from '@/components/LoadingSignal.vue';
import form from '@/mixins/form.js';

export default {
  name: 'APITokenLibrary',

  components: {
    BaseDialog,
    BaseActionCard,
    LoadingSignal,
  },

  mixins: [form],

  props: {
    editMode: {
      type: Boolean,
      required: true,
    },
    dense: {
      type: Boolean,
      default: false,
    },
    token_list: {
      type: Array,
      default: () => [],
    },
  },

  emits: ['reload', 'update:token_list'],

  data() {
    return {
      data_ready: true,
      search_text: undefined,
      show_new_api_token_form: false,
      show_new_api_token: false,
      show_delete: false,
      selected_token_key: '',
      token: '',
      token_description: '',
      token_expiry_date: null,
    };
  },

  computed: {
    selected_token() {
      return this.token_list.find((tk) => tk._key == this.selected_token_key);
    },
  },

  methods: {
    selectToken(token_key) {
      this.selected_token_key =
        this.selected_token_key == token_key ? null : token_key;
    },

    checkDate(d) {
      return date.isValid(d);
    },

    createToken() {
      if (!this.token_description || !this.token_expiry_date) {
        window.alert(this.$t('api_token_add_error_mandatory'));
        return;
      }

      this.show_new_api_token_form = false;

      this.$api
        .get('api-token', {
          params: {
            token_description: this.token_description,
            token_expiration: date.formatDate(
              this.token_expiry_date,
              'YYYY-MM-DDTHH:mm:ss.SSSZ',
            ),
          },
        })
        .then((data) => {
          this.token = data?.data?.access_token;
          if (this.token) {
            this.$emit('reload');
            this.selected_token_key = null;
            this.show_new_api_token = true;
          } else {
            this.closeAddTokenForm();
            this.$q.notify({
              message: this.$t('api_token_add_error_text'),
              color: 'theme-red',
              timeout: 1500,
              position: 'top',
            });
          }
        });
    },

    onClipboard() {
      copyToClipboard(this.token);
    },

    createTokenDone() {
      this.show_new_api_token = false;
    },

    deleteToken() {
      this.show_delete = false;

      this.$api.delete(`api-token/${this.selected_token_key}`).then(() => {
        this.$emit('reload');
        this.selected_token_key = null;
      });
    },

    closeAddTokenForm() {
      this.show_new_api_token_form = false;
      this.token_description = '';
      this.token_expiry_date = null;
    },

    formatDate(date_string) {
      if (!date_string) {
        return '';
      }
      const exp_date = DT.fromISO(date_string);
      if (exp_date < new Date()) {
        return 'EXPIRED';
      }
      return this.$formatDateTime(date_string, this.$i18n.locale, DT.DATE_MED);
    },
  },
};
</script>
