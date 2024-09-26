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
