<template>
  <div class="column q-px-md q-pb-sm fit">
    <!-- HEADER -->
    <div class="row items-center">
      <div
        class="text-h3 display highlight col-auto hover-underline q-mr-md"
        @click="goToProductPage"
      >
        {{ serial?.product?.code }}
      </div>
      <div v-if="!(edit_mode && can_edit)" class="text-h4 col-auto">
        {{ ' # ' + serial?.code }}
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
    </div>

    <div class="row q-mt-sm q-col-gutter-lg items-center text-h6">
      <div class="col-auto text-h5 text-low text-uppercase">
        {{ $t('creation_date') }}
      </div>
      <div class="col-auto">{{ serial_created_time_string }}</div>
      <div class="col-auto row items-center">
        <BaseUserAvatar
          :user="$store.getters.user_data(serial?.created_by)"
          size="24px"
          class="q-ml-md"
        />
      </div>
      <div class="col-auto q-ml-md hover-underline" @click="goToWorkOrderPage">
        {{ $t('work_order.short').toUpperCase() + ' ' + serial?.wo_code }}
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
          :root-path="`/media/serial/${serial_key}`"
          :disable="!(edit_mode && can_edit)"
          @update="field.value = $event"
        />
      </div>
    </template>
    <div v-else class="col-auto text-italic">No data</div>

    <q-space />

    <!-- ISSUE EVENTS -->
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
  </div>
</template>

<script>
import BaseUserAvatar from '@/components/BaseUserAvatar.vue';
import FormField from '@/components/FormField.vue';

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

  data() {
    return {
      history: [],
      loading: false,
      recording: false,
      base_path: '/media/user/',
      current_phase: 0,
      current_step: 0,
      data_column_width: 65,
    };
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
    this.getHistory();
  },

  methods: {
    getHistory() {
      this.$api
        .get('event', { params: { serial_key: this.serial_key } })
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
        query: {
          back_to: this.$route.name,
          ...this.$route.query,
        },
      });
    },
  },
};
</script>
