<template>
  <BaseDialog :show="true" maximized @close="exit">
    <q-card class="surface1 row" bordered square style="width: 95vw; height: 95vh">
      <!-- LEFT SECTION -->
      <div class="col-7 column full-height">
        <!-- HEADER -->
        <SerialHeader :serial="serial" @type-change="refreshSerial" />

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
            <div v-for="field in serial.data" :key="field._key" class="col-auto q-pr-md">
              <FormField :field="field" :root-path="`/media/serial/${serialKey}`" dense disable />
            </div>
          </template>
          <div v-else class="col-auto text-italic">No data</div>
        </div>

        <!-- PHASES -->
        <div class="row items-center q-pl-lg">
          <div class="col-auto text-h5 weight bold text-uppercase text-low">
            {{ $t('phase.phase') }}
          </div>
          <div class="col">
            <q-separator inset />
          </div>
        </div>

        <div class="col">
          <div class="scroll col q-py-sm full-width">
            <q-list id="phases" dense class="transparent medium text-left q-pl-sm" align="left">
              <q-item v-for="(phase, index) in serial.phases" :key="phase.phase_key" v-ripple clickable :name="index"
                :class="`full-width text-left ${editMode ? '' : 'undraggable'}`"
                @mouseenter="dragging ? undefined : (over_phase = index)"
                @mouseleave="dragging ? undefined : (over_phase = null)" @click="goToPhase(index)">
                <q-item-section avatar class="col-auto">
                  <q-avatar size="20px" :color="current_phase === index ? 'theme-blue' : 'theme-grey'
                    " class="display smaller" :class="{ highlight: current_phase === index }">
                    {{ index + 1 }}
                  </q-avatar>
                </q-item-section>

                <q-item-section>
                  <q-item-label class="display ellipsis" :class="current_phase === index
                    ? 'highlight'
                    : 'text-low weight-medium'
                    ">
                    {{ phase.alias }}
                  </q-item-label>
                </q-item-section>
              </q-item>
            </q-list>
          </div>
        </div>

        <!-- STEPS -->
        <div class="row items-center q-pl-lg">
          <div class="col-auto text-h5 weight bold text-uppercase text-low">
            {{ $t('phase.step') }}
          </div>
          <div class="col">
            <q-separator inset />
          </div>
        </div>

        <div class="col">
          <div class="scroll col q-py-sm full-width">
            <q-list id="phases" dense class="transparent medium text-left q-pl-sm" align="left">
              <q-item v-for="(phase, index) in serial.phases" :key="phase.phase_key" v-ripple clickable :name="index"
                :class="`full-width text-left ${editMode ? '' : 'undraggable'}`"
                @mouseenter="dragging ? undefined : (over_phase = index)"
                @mouseleave="dragging ? undefined : (over_phase = null)" @click="goToPhase(index)">
                <q-item-section avatar class="col-auto">
                  <q-avatar size="20px" :color="current_phase === index ? 'theme-blue' : 'theme-grey'
                    " class="display smaller" :class="{ highlight: current_phase === index }">
                    {{ index + 1 }}
                  </q-avatar>
                </q-item-section>

                <q-item-section>
                  <q-item-label class="display ellipsis" :class="current_phase === index
                    ? 'highlight'
                    : 'text-low weight-medium'
                    ">
                    {{ phase.alias }}
                  </q-item-label>
                </q-item-section>
              </q-item>
            </q-list>
          </div>
        </div>

        <q-space />

        <!-- ACTIONS -->
        <div class="row q-pa-md q-gutter-lg">
          <q-btn v-if="user_can_delete" color="theme-red" size="12px" icon="mdi-delete" :label="$t('delete')"
            @click="deleteSerial">
          </q-btn>
          <q-btn size="12px" icon="mdi-keyboard-return" color="theme-grey" :label="$t('back')" @click="exit">
          </q-btn>
        </div>
      </div>

      <q-separator vertical spaced />

      <!-- RIGHT SECTION -->
      <MessageThread :messages="messages" context="serial" :context_key="serial._key">
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
import SerialHeader from 'app/src/components/traceability/SerialHeader.vue';

export default {
  name: 'SerialDetail',

  components: {
    SerialHeader,
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
      recording: false,
      base_path: '/media/user/',
      current_phase: 0,
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
  },

  created() {
    this.$store.dispatch('loadUsers');
  },

  methods: {
    goToPhase(index) {
      this.current_phase = index;
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

    deleteSerial() {
      this.$q
        .dialog({
          cancel: true,
          title: this.$t('serial_delete_confirm_title'),
          message: this.$t('serial_delete_confirm_question'),
        })
        .onOk(() => {
          this.sendEvent({
            event_type: 'SERIAL_DELETED',
            event_data: {
              serial_data: {
                _key: this.serialKey,
              },
            },
          }).then(async () => {
            const work_order_key =
              this.$store.state.traceability.working_job_data.wo_key;
            await this.$store.dispatch('getSerials', { work_order_key });
            this.exit();
            this.notify({
              message: this.$t('serial_delete_success'),
            });
          });
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
