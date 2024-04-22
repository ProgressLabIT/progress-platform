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
            <div
              v-for="field in serial.data"
              :key="field._key"
              class="col-auto q-pr-md"
            >
              <FormField
                :field="field"
                :root-path="`/media/serial/${serialKey}`"
                dense
                disable
              />
            </div>
          </template>
          <div v-else class="col-auto text-italic">No data</div>
        </div>

        <!-- SERIAL EVENTS -->
        <div class="row items-center q-pl-lg">
          <div class="col-auto text-h5 weight bold text-uppercase text-low">
            {{ $t('history') }}
          </div>
          <div class="col">
            <q-separator inset />
          </div>
        </div>

        <q-list class="q-ml-lg q-px-xl col scroll q-pb-lg">
          <q-item
            v-for="(e, index) in history"
            :key="e._key"
            class="q-mt-md relative-position row justify-between full-width items-baseline"
          >
            <!-- TIMELINE DOT & LINE -->
            <div
              style="
                position: absolute;
                left: -30px;
                top: 13px;
                height: 100%;
                width: 32px;
              "
            >
              <div class="column full-height">
                <div class="dot"></div>
                <div v-if="index < history.length - 1" class="thread"></div>
              </div>
            </div>

            <!-- EVENT TYPE -->
            <q-item-section class="text-italic">
              {{ getHumanDate(e.timestamp) }}
            </q-item-section>
            <q-item-section class="text-h4 highlight text-uppercase">
              {{ $t(`events.${e.event_type}`) }}
            </q-item-section>
            <q-space />
            <q-item-section>
              <BaseUserAvatar name_first :user="getUserData(e)" />
            </q-item-section>
          </q-item>
        </q-list>

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
import BaseUserAvatar from '@/components/BaseUserAvatar.vue';
import FormField from '@/components/FormField.vue';
import MessageThread from '@/components/MessageThread.vue';
import SerialHeader from '@/components/SerialHeader.vue';
import event from '@/mixins/event.js';
import enrichSerial from '@/mixins/serials.js';

export default {
  name: 'SerialDetail',

  components: {
    SerialHeader,
    MessageThread,
    BaseUserAvatar,
    BaseDialog,
    FormField,
  },

  mixins: [enrichSerial, event],

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
    };
  },

  computed: {
    serial() {
      const serial_data = this.$store.getters.getSerialData(this.serialKey);
      return this.enrichSerial(serial_data);
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
    this.getHistory();
  },

  methods: {
    getHistory() {
      this.$api
        .get('event', { params: { serial_key: this.serial._key } })
        .then((resp) => (this.history = resp.data));
    },

    getAvatarSrc(user) {
      return (
        this.base_path + (user.name + user.surname).replace(/\s+/g, '') + '.jpg'
      );
    },

    getUserData(event) {
      const user = this.$store.getters.user_data(event.user_key);
      return {
        ...user,
        full_name: user.name + ' ' + user.surname,
        src: this.getAvatarSrc(user),
      };
    },

    getHumanDate(timestamp) {
      const config = {
        year: '2-digit',
        month: 'short',
        day: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
        second: '2-digit',
        weekday: 'short',
      };
      return this.$capitalize(
        this.$formatDateTime(timestamp, this.$i18n.locale, config),
      );
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

    closeSerial() {
      this.sendEvent({
        event_type: 'SERIAL_CLOSED',
        event_data: {
          serial_data: {
            _key: this.serial._key,
          },
        },
      }).then(() => {
        this.refreshSerial();
        this.notify({ message: this.$t('serial_update_success') });
      });
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
