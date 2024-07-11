<template>
  <BaseDialog :show="show">
    <q-card
      square
      class="surface1 q-pa-md"
      style="min-width: 600px; max-width: 800px"
    >
      <q-form ref="serial-form">
        <!-- FORM TITLE -->
        <q-card-section>
          <div class="row justify-between items-center">
            <div class="text-h2 display highlight text-center">
              {{ component_code }}
            </div>
          </div>
        </q-card-section>

        <!-- FORM BODY -->

        <BaseAutocompleteSerial
          v-for="n in batch_qt"
          :key="n"
          v-model="serialModel[n]"
          :label="$capitalize($t('serial'))"
          :product_key="component_key"
          :can_create="true"
        >
        </BaseAutocompleteSerial>

        <!-- FORM ACTIONS    navigation -->
        <q-card-section>
          <div class="row q-gutter-md">
            <q-btn
              color="theme-orange"
              :label="$t('save')"
              :loading="saving"
              @click="
                () => {
                  save();
                }
              "
            >
            </q-btn>

            <q-space />

            <q-btn color="theme-grey" :label="$t('cancel')" @click="cancel">
            </q-btn>
          </div>
        </q-card-section>
      </q-form>
    </q-card>
  </BaseDialog>
</template>

<script>
import BaseAutocompleteSerial from '@/components/BaseAutocompleteSerial.vue';
import BaseDialog from '@/components/BaseDialog.vue';
import { timestamp } from '@/lib/TimeHandling.js';

export default {
  name: 'SerialBomForm',

  components: {
    BaseDialog,
    BaseAutocompleteSerial,
  },

  props: {
    show: {
      type: Boolean,
      default: true,
    },
    component_code: {
      type: String,
      required: true,
    },
    component_key: {
      type: String,
      required: true,
    },
    batch_serials: {
      type: Array,
      default: () => [],
    },
    batch_qt: {
      type: String,
      required: true,
    },
  },

  emits: ['close', 'serialCreated'],

  data() {
    return {
      saving: false,
      enableSave: false,
      serialModel: [],
    };
  },

  computed: {
    session_data() {
      return this.$store.state.session;
    },
  },

  watch: {
    show: {
      handler() {
        this.initFormData();
      },
    },
  },

  async created() {
    this.initFormData();
  },

  methods: {
    async initFormData() {
      this.saving = false;
      this.enableSave = false;
      this.serialModel = [];
    },

    cancel() {
      this.initFormData();
      this.$emit('close');
    },

    async save() {
      this.saving = true;

      const event = {
        event_type: 'SERIAL_CREATED',
        user_session_key: this.session_data.session_key,
        timestamp: timestamp(),
      };

      await this.$api.post('event', event);

      this.cancel();
      this.saving = false;
    },
  },
};
</script>
