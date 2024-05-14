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
              {{ $t('serial_new_title') }}
            </div>
          </div>
        </q-card-section>

        <!-- FORM BODY -->

        <!-- form_step === 'select_product' -->
        <q-card-section
          v-if="form_step === 'select_product'"
          class="column q-gutter-md"
        >
          <!-- PRODUCT -->
          <BaseAutocompleteProduct
            :value="links.product"
            :hint="!phase_data ? $t('phase.no_phase') : null"
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
                {{ phase_data[phase_index].alias }}
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
                {{ phase_data[phase_index].steps[step_index].title }}
              </div>
            </template>
          </q-field>

          <FormField
            v-for="field in phase_data[phase_index].steps[step_index]
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
              @click="startSteps()"
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
      base_fields: [],
      confirmed: false,
      phase_data: null,
      counter_key: null,
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

  async created() {
    await this.initBaseFields();
    this.initFormData();
  },

  methods: {
    initFormData() {
      this.saving = false;
      this.enableSave = false;
      this.phase_index = 0;
      this.step_index = 0;
    },

    hasCustomField() {
      try {
        return (
          this.phase_data[this.phase_index].steps[this.step_index].form_fields
            .length > 0
        );
      } catch (error) {
        return false;
      }
    },

    startSteps() {
      this.form_step = 'fill_steps_data';
      this.step_index = 0;
      this.phase_index = 0;
      this.enableSaveButton();
    },

    nextTile() {
      if (
        this.step_index <
        this.phase_data[this.phase_index].steps.length - 1
      ) {
        this.step_index++;
      } else {
        if (this.phase_index < this.phase_data.length - 1) {
          this.step_index = 0;
          this.phase_index++;
        }
      }

      this.enableSaveButton();
    },

    enableSaveButton() {
      this.enableSave =
        this.step_index >= this.phase_data[this.phase_index].steps.length - 1 &&
        this.phase_index >= this.phase_data.length - 1;

      if (!this.enableSave && !this.hasCustomField()) {
        this.nextTile();
      }
    },

    prevTile() {
      this.enableSave = false;
      if (this.step_index > 0) {
        this.step_index--;
      } else if (this.phase_index > 0) {
        this.phase_index--;
        this.step_index = this.phase_data[this.phase_index].steps.length - 1;
      } else {
        this.form_step = 'select_product';
        this.enableSave = !this.phase_data;
      }

      if (
        this.phase_index > 0 &&
        this.step_index > 0 &&
        !this.hasCustomField()
      ) {
        this.prevTile();
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
      this.counter_key = product.counter_id;

      if (!product.process_phases) {
        return;
      }

      const { data: steps } = await this.$api.get(
        `product-steps/${product_key}`,
      );
      this.phase_data = steps;
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

    async save() {
      this.saving = true;

      let data = [];
      if (this.phase_data) {
        this.phase_data.forEach((phase) => {
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

      let serial_data = {
        data: data,
      };

      const user = this.session_data.user._key;

      serial_data.created_by = `User/${user}`; // temporarily hardcoding DB id

      if (this.links.product) {
        serial_data.product_key = this.links.product._key;
      }

      if (this.counter_key) {
        serial_data.counter_key = this.counter_key;
      }
      serial_data.user_key = this.session_data.user._key;

      const event = {
        event_type: 'SERIAL_CREATED',
        user_key: user,
        user_session_key: this.session_data.session_key,
        timestamp: timestamp(),
        serial_data,
      };

      await this.$api.post('event', event);

      this.cancel();
      this.saving = false;
    },
  },
};
</script>
