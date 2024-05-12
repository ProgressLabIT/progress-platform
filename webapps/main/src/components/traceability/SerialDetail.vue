<template>
  <BaseDialog :show="true" maximized @close="exit">
    <q-card
      class="surface1 row"
      bordered
      square
      style="width: 95vw; height: 95vh"
    >
      <!-- LEFT SECTION -->
      <div class="col-7 column full-height">
        <!-- HEADER -->
        <q-item class="q-py-md" :clickable="clickable">
          <q-item-section>
            <q-item-label class="row items-center">
              <span class="smaller text-body2 text-uppercase low-text q-ml-md">
                <span class="q-mr-sm">
                  {{ serial.serial }}
                </span>
                <span>#{{ serial._key }}</span>
              </span>
              <div class="col q-ml-xl">
                <q-btn
                  flat
                  round
                  icon="mdi-pencil"
                  :disable="editMode"
                  @click.stop="editMode = true"
                >
                  <q-tooltip>{{ $capitalize($t('edit')) }}</q-tooltip>
                </q-btn>
              </div>
            </q-item-label>
          </q-item-section>
        </q-item>

        <!-- FORM DATA -->
        <div class="row items-center q-pl-lg q-mt-sm">
          <div class="col-auto text-h5 weight bold text-uppercase text-low">
            {{ $t('form_title') }}
          </div>
          <div class="col">
            <q-separator inset />
          </div>
        </div>

        <div class="row q-px-lg q-pt-md q-mb-md">
          <template v-if="serial.data.length > 0">
            <FormField
              v-for="field in serial.data"
              :key="field._key"
              class="col-auto q-pr-md"
              :field="field"
              :root-path="`/media/serial/${serialKey}`"
              :disable="!editMode"
              dense
              @update="field.value = $event"
            />
          </template>
          <div v-else class="col-auto text-italic">No data</div>
        </div>

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

        <div class="row items-center q-pl-lg">
          <div class="col-5 column full-height">
            <div
              class="col-auto text-h5 weight bold text-uppercase text-low scroll"
            >
              <q-list
                id="phases"
                dense
                class="transparent medium text-left q-pl-sm"
                align="left"
              >
                <q-item
                  v-for="(phase, index) in serial.phases"
                  :key="phase.phase_key"
                  v-ripple
                  clickable
                  :name="index"
                  class="full-width text-left undraggable"
                  @mouseenter="dragging ? undefined : (over_phase = index)"
                  @mouseleave="dragging ? undefined : (over_phase = null)"
                  @click="goToPhase(index)"
                >
                  <q-item-section avatar class="col-auto">
                    <q-avatar
                      size="20px"
                      :color="
                        current_phase === index ? 'theme-blue' : 'theme-grey'
                      "
                      class="display smaller"
                      :class="{ highlight: current_phase === index }"
                    >
                      {{ index + 1 }}
                    </q-avatar>
                  </q-item-section>

                  <q-item-section>
                    <q-item-label
                      class="display ellipsis"
                      :class="
                        current_phase === index
                          ? 'highlight'
                          : 'text-low weight-medium'
                      "
                    >
                      {{ phase.alias }}
                    </q-item-label>
                  </q-item-section>
                </q-item>
              </q-list>
            </div>
          </div>

          <div
            class="col-auto text-h5 weight bold text-uppercase text-low scroll"
          >
            <q-list
              id="steps"
              dense
              class="transparent medium text-left q-pl-sm"
              align="left"
            >
              <q-item
                v-for="(step, index) in serial.phases[current_phase].steps"
                :key="step._key"
                v-ripple
                clickable
                :name="index"
                class="full-width text-left undraggable"
                @mouseenter="dragging ? undefined : (over_phase = index)"
                @mouseleave="dragging ? undefined : (over_phase = null)"
                @click="goToStep(index)"
              >
                <q-item-section avatar class="col-auto">
                  <q-avatar
                    size="20px"
                    :color="
                      current_step === index ? 'theme-blue' : 'theme-grey'
                    "
                    class="display smaller"
                    :class="{ highlight: current_step === index }"
                  >
                    {{ index + 1 }}
                  </q-avatar>
                </q-item-section>

                <q-item-section>
                  <q-item-label
                    class="display ellipsis"
                    :class="
                      current_step === index
                        ? 'highlight'
                        : 'text-low weight-medium'
                    "
                  >
                    {{ step.title }}
                  </q-item-label>
                </q-item-section>
              </q-item>
            </q-list>
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

        <div class="row q-px-lg q-pt-md q-mb-md">
          <template
            v-if="
              serial &&
              serial.phases[current_phase] &&
              serial.phases[current_phase].steps[current_step] &&
              serial.phases[current_phase].steps[current_step].form_fields
            "
          >
            <FormField
              v-for="field in serial.phases[current_phase].steps[current_step]
                .form_fields"
              :key="field._key"
              class="col-auto q-pr-md"
              :field="field"
              :root-path="`/media/serial/${serialKey}`"
              :disable="!editMode"
              dense
              @update="field.value = $event"
            />
          </template>
          <div v-else class="col-auto text-italic">No data</div>
        </div>
        <q-space />

        <!-- ACTIONS -->
        <div class="row q-pa-md q-gutter-lg">
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
            :disable="!editMode"
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

      <q-separator vertical spaced />

      <!-- RIGHT SECTION -->
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
    </q-card>
  </BaseDialog>
</template>

<script>
import BaseDialog from '@/components/BaseDialog.vue';
import FormField from '@/components/FormField.vue';
import { timestamp } from '@/lib/TimeHandling.js';

export default {
  name: 'SerialDetail',

  components: {
    BaseDialog,
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
      return this.$store.getters.hasPermission('production');
    },

    session_data() {
      return this.$store.state.session;
    },
  },

  created() {
    this.editMode = false;
    this.saving = false;
    this.$store.dispatch('loadUsers');
  },

  methods: {
    goToPhase(index) {
      this.current_phase = index;
      this.current_step = 0;
    },

    goToStep(index) {
      this.current_step = index;
    },

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
