<template>
  <LoadingSignal v-if="!data_ready" />

  <div v-else class="row full-height">
    <div class="full-height column col">
      <div
        class="row q-mt-md q-px-lg q-py-sm text-h6 text-uppercase weight-bold"
      >
        <div class="col-3">
          {{ $t('context') }}
        </div>
        <div class="col">
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
            {{ $capitalize(tk.context) }}
          </div>
          <div class="col">
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
      @close="show_new_api_token_form = false"
    >
      <BaseActionCard
        :title="$t('api_token_add')"
        :save-label="$t('confirm')"
        @save="createToken"
        @cancel="show_new_api_token_form = false"
      >
        {{ $t('api_token_add_text') }}
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
import { copyToClipboard } from 'quasar';
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

    createToken() {
      this.show_new_api_token_form = false;

      this.$api.get('api-token').then((data) => {
        this.token = data?.data?.access_token;
        this.$emit('reload');
        this.selected_token_key = null;
        this.show_new_api_token = true;
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
  },
};
</script>
