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
              <template v-if="mode === 'new'">
                {{ $t('serial_new_title') }}
              </template>
              <template v-else>
                {{ $t('serial_update_title') }}
              </template>
            </div>
          </div>
        </q-card-section>

        <!-- FORM BODY -->

        <!-- form_step === 'select_product' -->
        <q-card-section
          v-if="mode === 'new' && form_step === 'select_product'"
          class="column q-gutter-md"
        >
          <!-- PRODUCT -->
          <BaseAutocompleteProduct
            :value="links.product"
            :hint="!step_data ? $t('phase.no_phase') : null"
            key-only
            :label="$capitalize($t('product.label'))"
            @select="(selection) => loadProduct(selection)"
          />

          <FormField
            v-for="field in form_fields"
            :key="field._key"
            :field="field"
            :root-path="`/media/serial/${serial?._key}`"
            @update="field.value = $event"
          />
        </q-card-section>

        <!-- SERIAL DATA -->
        <q-card-section v-else key="serial_data">
          <!-- FORM FIELDS -->
          <div class="text-h3"></div>

          <q-field
            filled
            :label="$t('phase.phase')"
            stack-label
            disable
            class="q-mb-lg"
          >
            <template #control>
              <div class="self-center full-width no-outline" tabindex="0">
                {{ step_data[phase_index].alias }}
              </div>
            </template>
          </q-field>

          <q-field
            filled
            :label="$t('phase.step')"
            stack-label
            class="q-mb-lg"
            disable
          >
            <template #control>
              <div class="self-center full-width no-outline" tabindex="0">
                {{ step_data[phase_index].steps[step_index].title }}
              </div>
            </template>
          </q-field>

          <FormField
            v-for="field in step_data[phase_index].steps[step_index]
              .form_fields"
            :key="field._key"
            :field="field"
            :root-path="`/media/serial/${serial?._key}`"
            @update="field.value = $event"
          />
        </q-card-section>

        <!-- FORM ACTIONS    navigation -->
        <q-card-section>
          <div class="row q-gutter-md">
            <q-btn
              v-if="form_step === 'select_product'"
              color="theme-blue"
              :label="$t('next')"
              :disable="!links.product"
              @click="form_step = 'fill_steps_data'"
            >
            </q-btn>
            <template v-else>
              <q-btn
                icon="mdi-arrow-left-bold"
                color="theme-blue"
                @click="prevTile()"
              >
              </q-btn>
              <q-btn
                v-if="!enableSave && form_step === 'fill_steps_data'"
                icon="mdi-arrow-right-bold"
                color="theme-blue"
                @click="nextTile()"
              >
              </q-btn>

              <q-btn
                v-else
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
            </template>

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
import BaseAutocompleteProduct from '@/components/BaseAutocompleteProduct.vue';
import BaseDialog from '@/components/BaseDialog.vue';
import FormField from '@/components/FormField.vue';
import { timestamp } from '@/lib/TimeHandling.js';

export default {
  name: 'SerialForm',

  components: {
    BaseAutocompleteProduct,
    BaseDialog,
    FormField,
  },

  props: {
    show: {
      type: Boolean,
      default: true,
    },
    mode: {
      type: String,
      default: 'new',
    },
    serial: {
      type: Object,
      default: undefined,
    },
  },

  emits: ['close', 'serialCreated'],

  data() {
    return {
      phase_index: 0,
      step_index: 0,
      saving: false,
      enableSave: false,
      form_step: 'select_product',
      form_fields: [],
      base_fields: [],
      confirmed: false,
      step_data: null,
      links: {
        product: null,
        user: null,
      },
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

  created() {
    this.initBaseFields();
    this.initFormData();
  },

  methods: {
    initFormData() {
      const form_template = this.base_fields ?? [];
      this.saving = false;
      this.enableSave = false;
      this.phase_index = 0;
      this.step_index = 0;
      const use_clean_form = this.mode === 'new';
      if (use_clean_form) {
        this.links.product = null;
        // Use fields from serial type template adding empty value
        // If no template, force null, otherwise `undefined` will not be included in the api body and the serial data will not be updated
        this.form_fields = form_template.map((field) => ({
          ...field,
          value: null,
        }));
        return;
      }

      this.form_fields = form_template.map((field) => ({
        ...field,
        value: this.serial.data.find(({ _key }) => _key === field._key)?.value,
      }));
    },

    async initBaseFields() {
      const { data: fields } = await this.$api.get('serial-field');
      this.base_fields = fields;
    },

    nextTile() {
      if (this.step_index < this.step_data[this.phase_index].steps.length - 1) {
        this.step_index++;
      } else {
        if (this.phase_index < this.step_data.length - 1) {
          this.step_index = 0;
          this.phase_index++;
        }
      }

      this.enableSave =
        this.step_index >= this.step_data[this.phase_index].steps.length - 1 &&
        this.phase_index >= this.step_data.length - 1;
    },

    prevTile() {
      this.enableSave = false;
      if (this.step_index > 0) {
        this.step_index--;
      } else if (this.phase_index > 0) {
        this.phase_index--;
        this.step_index = this.step_data[this.phase_index].steps.length - 1;
      } else {
        this.form_step = 'select_product';
        this.enableSave = !this.step_data;
      }
    },

    async loadProduct(product_key) {
      if (product_key === null) {
        this.links.product = null;
        return;
      }
      // To avoid loading in advance a lot of unnecessary product data, the product list contains limited information.
      // So, it is necessary to fetch the full product data first and then load the stepss options.
      const { data: product } = await this.$api.get(`product/${product_key}`);

      this.links.product = product;

      if (!product.process_phases) {
        return;
      }

      const { data: steps } = await this.$api.get(
        `product-steps/${product_key}`,
      );
      this.step_data = steps;
      this.phase_index = 0;
      this.step_index = 0;
    },

    cancel() {
      this.initFormData();
      this.form_step = 'select_product';
      this.$emit('close');
    },

    /**
     * @param {import('@/types/form').FormField} field
     * @returns {string | undefined}
     */
    getFieldType(field) {
      return this.$store.getters.getCustomFieldByKey(field._key)?.type;
    },

    async save() {
      this.saving = true;

      const serial_data = {
        data: this.form_fields.map((field) => ({
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
        })),
      };

      const user = this.session_data.user._key;

      if (this.mode === 'new') {
        // if link is active send data in the form e.g. { type: product, key: whatever }
        serial_data.created_by = `User/${user}`; // temporarily hardcoding DB id

        // Map links to list of objects, including only populated properties
        const links = [];
        Object.entries(this.links).forEach(([key, value]) => {
          if (value) {
            links.push({ type: key, key: value._key });
          }
        });
        serial_data.linked_to = links;
      } else {
        serial_data._key = this.serial._key;
      }

      const event = {
        event_type: this.mode === 'new' ? 'SERIAL_CREATED' : 'SERIAL_UPDATED',
        user_key: user,
        user_session_key: this.session_data.session_key,
        timestamp: timestamp(),
        serial_data,
      };

      await this.$api.post('event', event);
      /*const { data } = await this.$api.post('event', event);
      const message =
        this.mode === 'new' ? 'serial_new_success' : 'serial_update_success';

      const serial_key =
        this.mode === 'new' ? data.detail.serial_key : serial_data._key;
      await this.saveFiles(serial_key);*/

      // If from work session, fetch serials directly, otherwise signal the parent component to do so
      /*if (!this.with_links) {
        await this.$store.dispatch('getSerials', {
          work_order_key: this.job_data.wo_key,
        });
      } else {
        this.$emit('serialCreated');
      }*/
      this.cancel();
      this.saving = false;
      /*this.$q.notify({
        message: this.$t(message),
        color: 'theme-orange',
        timeout: 1500,
        position: 'top',
      });*/
    },
  },
};
</script>
