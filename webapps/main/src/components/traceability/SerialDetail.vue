<template>
  <BaseModalScreen :show="true" @close="exit">
    <template #header>
      <span
        class="q-ml-md display medium highlight weight-medium text-uppercase"
      >
        {{ $t('serial_id') }}: {{ serial._key }}
      </span>

      <q-space></q-space>
    </template>

    <template #content>
      <q-splitter
        v-model="data_column_width"
        class="fit q-py-sm"
        separator-class="text-disabled"
      >
        <template #before>
          <div class="column q-pa-md fit">

            <!-- HEADER -->
            <div class="row justify-between items-center">
              <div v-if="!can_edit" class="text-h3 display highlight">
                {{ serial.serial }}
              </div>
              <q-input
                v-else
                v-model="serial.serial"
                filled
                dense
                size="70"
                class="input-uppercase"
              >
              </q-input>

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

            <!-- FORM DATA -->
            <div class="col-auto text-h5 text-uppercase text-low q-mt-lg">
              {{ $t('form_title') }}
            </div>

            <template v-if="serial.data.length > 0">
              <div class="column col scroll">
                <div class="row full-width q-col-gutter-md">
                <div class="col-4"
                  v-for="field in serial.data"
                  :key="field.form_field_key"
                >
                  <FormField
                    :field="field"
                    :root-path="`/media/serial/${serialKey}`"
                    :disable="!can_edit"
                    dense
                    @update="field.value = $event"
                  />
                </div>
              </div>
            </div>
            </template>
            <div v-else class="col-auto text-italic">No data</div>

            <!-- PHASES & STEPS -->
            <div class="row items-center q-pl-lg">
              <div class="col-5 column full-height">
                <div class="col-auto text-h5 weight bold text-uppercase text-low">
                  {{ $t('phase.phase') }}
                </div>

                <div class="col">
                  <q-separator inset />
                </div>
              </div>

              <div class="col-auto text-h5 weight bold text-uppercase text-low">
                {{ $t('phase.step') }}
              </div>

              <div class="col">
                <q-separator inset />
              </div>
            </div>


            <!-- STEPS DATA -->
            <div class="row items-center q-pl-lg q-mt-sm">
              <div class="col-auto text-h5 weight bold text-uppercase text-low">
                {{ $t('form_title') }}
              </div>
              <div class="col">
                <q-separator inset />
              </div>
            </div>


            <q-space />

            <!-- ACTIONS -->
            <div class="row q-gutter-md">
              <q-btn
                v-if="user_can_delete"
                color="theme-red"
                size="12px"
                icon="mdi-delete"
                :label="$t('delete')"
                @click="deleteSerial"
              >
              </q-btn>
              <q-btn
                size="12px"
                color="theme-orange"
                :label="$t('save')"
                :loading="saving"
                :disable="!can_edit"
                @click="save"
              >
              </q-btn>
              <q-btn
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
import FormField from '@/components/FormField.vue';
import MessageThread from '@/components/MessageThread.vue';
import { timestamp } from '@/lib/TimeHandling.js';

export default {
  name: 'SerialDetail',

  components: {
    BaseModalScreen,
    MessageThread,
    FormField,
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
      data_column_width: 65
    };
  },

  computed: {
    serial() {
      return this.$store.getters.getSerialData(this.serialKey);
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
    console.log(this.$store.state.serial)
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
      this.getHistory();
    },

    getFormFieldValue(phase_key, step_key, fields) {
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
    },

    getFieldType(field) {
      return this.$store.getters.getCustomFieldByKey(field._key)?.type;
    },

    async save() {
      this.saving = true;

      let phase_data = this.serial.phases;

      let data = [];
      if (phase_data) {
        phase_data.forEach((phase) => {
          if (phase.steps) {
            phase.steps.forEach((step) => {
              data = data.concat(
                this.getFormFieldValue(
                  phase.phase_key,
                  step._key,
                  step.form_fields,
                ),
              );
            });
          }
        });
      }

      let serial_data = this.serial;
      serial_data.data = data;

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

      this.saving = false;
      this.exit();
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
