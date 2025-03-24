<template>
  <div class="column q-px-md fit">
    <!-- HEADER -->
    <div class="row items-center">
      <div
        class="text-h3 display highlight col-auto hover-underline q-mr-md"
        @click="goToProductPage"
      >
        {{ serial?.product?.code }}
      </div>
      <div
        v-if="!(edit_mode && can_edit && config.allowSerialCodeEdit)"
        class="text-h4 col-auto text-uppercase"
      >
        {{ ' # ' + serial?.code }}
      </div>
      <q-input
        v-else
        :model-value="serial.code"
        dense
        filled
        :label="$t('serial.code')"
        class="input-uppercase"
        @update:model-value="(v) => (serial.code = v.toUpperCase())"
      >
      </q-input>

      <q-space></q-space>

      <q-chip
        :color="serialAvailable ? 'theme-green' : 'theme-grey'"
        class="smaller text-uppercase highlight">
        {{ serialAvailable ? $t('available') : $t('unavailable') }}
      </q-chip>

      <q-btn
        v-if="printAvailable"
        flat
        round
        icon="mdi-printer"
        class="q-ml-sm"
        @click.stop="openPrintDialog"
      >
        <q-tooltip>{{ $capitalize($t('print')) }}</q-tooltip>
      </q-btn>
    </div>

    <!-- SUB HEADER -->
    <div class="row q-pt-md q-col-gutter-lg items-center text-h6">
      <div class="col-auto text-h5 text-low text-uppercase">
        {{ $t('creation_date') }}
      </div>
      <div class="col-auto">{{ serial_created_time_string }}</div>
      <div class="col-auto row items-center">
        <BaseUserAvatar
          :user="$store.getters.user_data(serial?.user_key)"
          size="24px"
          class="q-ml-md"
        />
      </div>
      <div class="col-auto q-ml-md hover-underline" @click="goToWorkOrderPage">
        {{ $t('work_order.short').toUpperCase() + ' ' + serial?.wo_code }}
      </div>
    </div>

    <!-- SERIAL DATA -->
    <q-tabs
      v-model="tab"
      dense
      class="q-mt-md text-low"
      content-class="text-h5"
      indicator-color="theme-blue"
      align="left"
      active-class="text-high weight-bold"
    >
      <q-tab name="form" :label="$t('serial_data')" class="text-left" />
      <q-tab name="history" :label="$t('history')" />
    </q-tabs>

    <q-card square class="col surface2 scroll">
      <q-tab-panels v-model="tab" class="transparent">
        <!-- SERIAL FORM DATA -->
        <q-tab-panel name="form">
          <template v-if="serial.data.length > 0">
            <div class="column col scroll q-pt-sm">
              <FormField
                v-for="field in serial.data"
                :key="field._key"
                :field="field"
                :root-path="`/media/serial/${serial_key}/${field._key}`"
                :disable="!(edit_mode && can_edit)"
                @update="field.value = $event"
              />
            </div>
          </template>
          <div v-else class="col-auto text-italic">No data</div>
        </q-tab-panel>

        <!-- ISSUE EVENTS -->
        <q-tab-panel name="history">
          <q-list class="q-pl-xl col scroll q-pb-lg">
            <q-item
              v-for="(e, index) in history"
              :key="e._key"
              class="q-mt-md relative-position row justify-between full-width items-baseline"
            >
              <!-- TIMELINE DOT & THREAD -->
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

              <!-- TIMESTAMP -->
              <q-item-section
                class="text-italic q-pr-sm"
                style="max-width: 200px"
              >
                {{ getHumanDate(e.timestamp) }}
              </q-item-section>

              <!-- EVENT TYPE -->
              <q-item-section class="text-h4 highlight text-uppercase">
                {{ $t(`events.${e.event_type}`) }}
              </q-item-section>

              <!-- EVENT USER -->
              <q-item-section class="col-auto">
                <BaseUserAvatar name_first :user="getUserData(e)" />
              </q-item-section>
            </q-item>
          </q-list>
        </q-tab-panel>
      </q-tab-panels>
    </q-card>
  </div>
</template>

<script>
import { storeToRefs } from 'pinia';
import BaseUserAvatar from '@/components/BaseUserAvatar.vue';
import FormField from '@/components/FormField.vue';
import { usePrintDialog } from '@/lib/print';
import { useConfigStore } from '@/stores/config';

export default {
  name: 'SerialDetailForm',

  components: {
    BaseUserAvatar,
    FormField,
  },

  props: {
    // from router
    serial_key: {
      type: String,
      required: true,
    },

    edit_mode: {
      type: Boolean,
      required: true,
    },
  },

  emits: ['exit'],

  setup(props) {
    const { config } = storeToRefs(useConfigStore());

    const { open: openPrintDialog, isAvailable } = usePrintDialog({
      context: 'serial',
      contextData: props.serial_key,
    });

    return {
      config,
      openPrintDialog,
      printAvailable: isAvailable,
    };
  },

  data() {
    return {
      tab: 'form',
      history: [],
      loading: false,
      recording: false,
      base_path: '/media/user/',
      current_phase: 0,
      current_step: 0,
      data_column_width: 65,
      events: NaN,
      serialAvailable: false,
    };
  },

  watch: {
    serial_key: {
      immediate: true,
      handler() {
        this.getInfo();
      },
    },
  },

  computed: {
    serial() {
      return this.$store.getters.getSerialData(this.serial_key);
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
        this.$formatDateTime(this.serial?.created, this.$i18n.locale, config),
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

    session_data() {
      return this.$store.state.session;
    },

    can_edit() {
      return !this.$store.getters.getSerialData(this.serial_key).deleted;
    },
  },

  created() {
    this.$store.dispatch('loadUsers');
    this.getInfo();
    let eventURL =
      this.$api.defaults.baseURL + '/notification/serial-notification';
    this.events = new EventSource(eventURL, {
      withCredentials: false,
    });
    this.events.addEventListener('serial-notification', (event) => {
      this.handleMessage(event);
    });
  },

  beforeUnmount() {
    if (this.events) {
      this.events.close();
    }
  },

  methods: {
    getInfo() {
      // Get history
      this.$api
        .get('event', { params: { serial_key: this.serial_key } })
        .then((resp) => (this.history = resp.data));

      // Get inventory availability
      this.$api.get('inventory', { params: { serial_key: this.serial_key } })
      .then((resp) => {
        this.serialAvailable = resp.data.length > 0
      })
      .catch((err) => {
        console.log(err.response.data.message);
      });
    },

    handleMessage(message) {
      let event = JSON.parse(message.data);
      if (event?.serial_key === this.serial_key) {
        this.getInfo();
      }
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

    getFieldType(field) {
      return this.$store.getters.getCustomFieldByKey(field.custom_field_key)
        ?.type;
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

    goToProductPage() {
      this.$router.push({
        name: 'productHome',
        params: {
          product_key: this.serial.product_key,
        },
      });
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
  border: 5px solid var(--surface-2)
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
