<template>
  <BaseModalScreen :show="true" @close="exit">
    <template #header>
      <q-btn
        dense
        unelevated
        icon="mdi-file-tree"
        @click="mini_state = !mini_state"
      />
      <span
        class="q-ml-md display medium highlight weight-medium text-uppercase"
      >
        {{ $t('serial_id') }}: {{ serial._key }}
      </span>

      <q-space></q-space>
    </template>

    <template #content>
      <SerialTree :mini_state="mini_state"></SerialTree>
      <q-splitter
        v-model="data_column_width"
        class="fit q-py-sm"
        separator-class="text-disabled"
      >
        <template #before>
          <div class="column q-px-md q-pb-sm fit">
            <!-- HEADER -->
            <div class="row items-center">
              <div
                class="text-h3 display highlight col-auto hover-underline q-mr-md"
                @click="goToProductPage"
              >
                {{ serial.product.code }}
              </div>
              <div v-if="!can_edit" class="text-h4 col-auto">
                {{ ' # ' + serial.code }}
              </div>
              <q-input
                v-else
                v-model="serial.code"
                filled
                :label="$t('serial.code')"
                size="70"
                class="input-uppercase"
              >
              </q-input>

              <q-space></q-space>
              <q-btn
                v-if="!serial.deleted"
                flat
                round
                icon="mdi-pencil"
                :disable="editMode"
                @click.stop="editMode = true"
              >
                <q-tooltip>{{ $capitalize($t('edit')) }}</q-tooltip>
              </q-btn>
            </div>

            <div class="row q-mt-sm q-col-gutter-lg items-center text-h6">
              <div class="col-auto text-h5 text-low text-uppercase">
                {{ $t('creation_date') }}
              </div>
              <div class="col-auto">{{ serial_created_time_string }}</div>
              <div class="col-auto row items-center">
                <BaseUserAvatar
                  :user="$store.getters.user_data(serial.created_by)"
                  size="24px"
                  class="q-ml-md"
                />
              </div>
              <div
                class="col-auto q-ml-md hover-underline"
                @click="goToWorkOrderPage"
              >
                {{
                  $t('work_order.short').toUpperCase() + ' ' + serial.wo_code
                }}
              </div>
            </div>

            <!-- FORM DATA -->
            <div class="col-auto text-h5 text-uppercase text-low q-mt-lg">
              {{ $t('serial_data') }}
            </div>

            <template v-if="serial.data.length > 0">
              <div class="column col scroll q-py-md q-mb-md">
                <FormField
                  v-for="field in serial.data"
                  :key="field._key"
                  :field="field"
                  :root-path="`/media/serial/${serialKey}`"
                  :disable="!can_edit"
                  @update="field.value = $event"
                />
              </div>
            </template>
            <div v-else class="col-auto text-italic">No data</div>

            <q-space />

            <!-- ACTIONS -->
            <div class="row q-gutter-md">
              <q-btn
                v-if="user_can_delete && !editMode"
                color="theme-red"
                size="12px"
                icon="mdi-delete"
                :label="$t('delete')"
                @click="deleteSerial"
              >
              </q-btn>
              <q-btn
                v-if="editMode"
                size="12px"
                color="theme-orange"
                :label="$t('save')"
                :loading="saving"
                :disable="!can_edit"
                @click="save"
              >
              </q-btn>
              <q-btn
                v-if="editMode"
                size="12px"
                color="theme-grey"
                :label="$t('cancel')"
                :loading="saving"
                @click="onDialogCancel"
              >
              </q-btn>
              <q-btn
                v-if="!editMode"
                size="12px"
                icon="mdi-keyboard-return"
                color="theme-grey"
                :label="$t('back')"
                @click="exit"
              >
              </q-btn>
            </div>
          </div>
        </template>

        <!-- RIGHT SECTION -->
        <template #after>
          <MessageThread
            :messages="messages"
            context="serial"
            :context_key="serial._key"
          >
            <template #header>
              <div class="display low-text text-h5 col-auto q-pb-md">
                {{ $t('message', 2) }}
              </div>
              <q-separator></q-separator>
            </template>
          </MessageThread>
        </template>
      </q-splitter>
    </template>
  </BaseModalScreen>
</template>

<script>
import BaseModalScreen from '@/components/BaseModalScreen.vue';
import BaseUserAvatar from '@/components/BaseUserAvatar.vue';
import FormField from '@/components/FormField.vue';
import MessageThread from '@/components/MessageThread.vue';
import SerialTree from '@/components/traceability/SerialTree.vue';
import { timestamp } from '@/lib/TimeHandling.js';

export default {
  name: 'SerialDetail',

  components: {
    BaseModalScreen,
    BaseUserAvatar,
    MessageThread,
    FormField,
    SerialTree,
  },

  props: {
    // from router
    serialKey: {
      type: String,
      required: true,
    },
  },

  data() {
    return {
      messages: [],
      history: [],
      loading: false,
      saving: false,
      recording: false,
      base_path: '/media/user/',
      current_phase: 0,
      current_step: 0,
      editMode: false,
      data_column_width: 65,
      mini_state: false,
    };
  },

  computed: {
    serial() {
      return this.$store.getters.getSerialData(this.serialKey);
    },

    serial_created_time_string() {
      const config = {
        year: '2-digit',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      };
      return this.$capitalize(
        this.$formatDateTime(this.serial.created, this.$i18n.locale, config),
      );
    },

    form_fields() {
      const form_template = this.form_template ?? [];
      return form_template.map((field) => ({
        ...field,
        value: this.serial.data.find(
          ({ form_field_key }) => form_field_key === field._key,
        )?.value,
      }));
    },

    created_by() {
      const user_key = this.serial.created_by.split('/')[1];
      return this.$store.getters.user_data(user_key);
    },

    user_can_delete() {
      return (
        this.$store.getters.hasPermission('production') &&
        !this.$store.getters.getSerialData(this.serialKey).deleted
      );
    },

    session_data() {
      return this.$store.state.session;
    },

    can_edit() {
      return (
        this.editMode &&
        !this.$store.getters.getSerialData(this.serialKey).deleted
      );
    },
  },

  created() {
    this.editMode = false;
    this.saving = false;
    this.$store.dispatch('loadUsers');
    console.log(this.$store.state.serial);
  },

  methods: {
    notify({ message, color = 'theme-green' }) {
      this.$q.notify({
        message,
        color,
        timeout: '1500',
        position: 'top',
      });
    },

    refreshSerial() {
      this.$store.dispatch('getSerials', { serial_key: this.serialKey });
      //this.getHistory();
    },

    /*getFormFieldValue(phase_key, step_key, fields) {
      return fields.map((field) => ({
        phase_key: phase_key,
        step_key: step_key,
        form_field_key: field._key,
        custom_field_key: field.custom_field_key,
        value:
          this.getFieldType(field) === 'files'
            ? field.value
                ?.filter((file) => !file.delete)
                .map((file) => ({
                  size: file.size,
                  name: file.name,
                }))
            : field.value,
      }));
    },*/

    getFieldType(field) {
      return this.$store.getters.getCustomFieldByKey(field.custom_field_key)
        ?.type;
    },

    async onDialogCancel() {
      this.refreshSerial();
      this.editMode = false;
    },

    missingMandatoryValues(form_data) {
      let missing_mandatory_fields = false;
      if (!form_data) {
        return missing_mandatory_fields;
      }
      form_data.forEach((field) => {
        let type = this.getFieldType(field);
        if (
          type !== 'ternary' &&
          field.mandatory &&
          (!field.value || field.value === null || field.value === '')
        ) {
          missing_mandatory_fields = true;
        }
      });
      return missing_mandatory_fields;
    },

    async save() {
      this.saving = true;

      let serial_data = this.serial;

      if (this.missingMandatoryValues(this.serial.data)) {
        window.alert(this.$t('fill_mandatory_fields'));
        this.saving = false;
        return;
      }

      const user = this.session_data.user._key;

      serial_data.updated_by = `User/${user}`; // temporarily hardcoding DB id

      const event = {
        event_type: 'SERIAL_UPDATED',
        user_key: user,
        user_session_key: this.session_data.session_key,
        timestamp: timestamp(),
        serial_data,
      };

      await this.$api.post('event', event);

      this.editMode = false;
      this.saving = false;
    },

    deleteSerial() {
      this.$q
        .dialog({
          cancel: true,
          title: this.$t('serial_delete_confirm_title'),
          message: this.$t('serial_delete_confirm_question'),
        })
        .onOk(() => {
          const user = this.session_data.user._key;

          const event = {
            event_type: 'SERIAL_DELETED',
            user_key: user,
            user_session_key: this.session_data.session_key,
            timestamp: timestamp(),
            serial_data: {
              _key: this.serial._key,
            },
          };

          this.$api.post('event', event);
          this.exit();
        });
    },

    goToProductPage() {
      this.$router.push({
        name: 'productHome',
        params: {
          product_key: this.serial.product_key,
        },
        query: {
          back_to: this.$route.name,
          ...this.$route.query,
        },
      });
    },

    goToWorkOrderPage() {
      this.$router.push({
        name: 'workOrderScreen',
        params: {
          wo_key: this.serial.wo_key,
        },
        query: {
          back_to: this.$route.name,
          ...this.$route.query,
        },
      });
    },

    exit() {
      this.$router.back();
    },
  },
};
</script>

<style lang="sass" scoped>
.dot
  height: 13px
  width: 13px
  border-radius: 100%
  background-color: #888
  border: 5px solid var(--surface-1)
  box-sizing: content-box
  z-index:99

.thread
  position: absolute
  height: 100%
  left: 11px
  top: 20px
  width: 1px
  background-color: #fff3
</style>
