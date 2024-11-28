<template>
  <BaseDialog :show="show" @close="cancel">
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
            :disable="force_serial_code !== null"
            :filter-origin="(p) => p.traceability_level !== null"
            @select="(selection) => loadProduct(selection)"
          />

          <q-field
            v-if="force_serial_code"
            :label="force_serial_code"
            stack-label
          >
          </q-field>
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
                {{ phase_data[phase_index]?.steps[step_index]?.title }}
              </div>
            </template>
          </q-field>

          <FormField
            v-for="field in phase_data[phase_index]?.steps[step_index]
              ?.form_fields"
            :key="field._key"
            :field="field"
            :root-path="`/media/serial/${serial?._key}/${field._key}`"
            @update="field.value = $event"
          />
        </q-card-section>

        <!-- FORM ACTIONS    navigation -->
        <q-card-section>
          <div class="row q-gutter-md">
            <q-btn
              v-if="form_step === 'select_product' && has_fields"
              color="theme-blue"
              :label="$t('next')"
              :disable="!links.product"
              @click="startSteps()"
            >
            </q-btn>
            <q-btn
              v-if="form_step === 'select_product' && !has_fields"
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
            <template v-else>
              <q-btn
                v-if="form_step === 'fill_steps_data'"
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
                v-else-if="enableSave"
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
    auto_link_product: {
      type: String,
      default: null,
    },
    force_serial_code: {
      type: String,
      default: null,
    },
  },

  emits: ['close', 'serialCreated'],

  data() {
    return {
      phase_index: 0,
      has_fields: true,
      step_index: 0,
      saving: false,
      enableSave: false,
      form_step: 'select_product',
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
    this.initFormData();
  },

  methods: {
    initFormData() {
      this.saving = false;
      this.enableSave = false;
      this.phase_index = 0;
      this.step_index = 0;

      this.links.product = null;

      if (this.auto_link_product != null) {
        this.loadProduct(this.auto_link_product);
      }
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
      this.counter_key = product.counter_key;

      if (!product.process_phases) {
        return;
      }

      const { data: steps } = await this.$api.get(
        `product/${product_key}/process`,
      );
      this.phase_data = steps;

      let hasCustomField = false;

      if (this.phase_data) {
        this.phase_data.forEach((phase) => {
          if (phase.steps) {
            phase.steps.forEach((step) => {
              if (!hasCustomField) {
                hasCustomField = step.form_fields?.length > 0;
              }
            });
          }
        });
      }

      this.has_fields = hasCustomField;
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
      return this.$store.getters.getCustomFieldByKey(field.custom_field_key)
        ?.type;
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

    async saveFiles(serial_key) {
      let form_fields = [];
      if (this.phase_data) {
        this.phase_data.forEach((phase) => {
          if (phase.steps) {
            phase.steps.forEach((step) => {
              form_fields.push(...step.form_fields);
            });
          }
        });
      }

      const promises = form_fields
        .filter((field) => this.getFieldType(field) === 'files')
        .map(async (field) => {
          const to_delete = [];
          const to_add = [];

          field.value?.forEach((file) => {
            if (file.temp) {
              to_add.push(file.content);
            } else if (file.delete) {
              to_delete.push(file.name);
            }
          });

          const target = {
            bucket: 'serial',
            object_key: serial_key,
            subfolder: field._key,
          };

          // Upload new files
          if (to_add.length) {
            // Populate form data
            const add_body = new FormData();
            Object.entries(target).forEach(([k, v]) => add_body.append(k, v));
            to_add.forEach((file) => add_body.append('contents', file));
            // Post files
            try {
              await this.$api.post('/files', add_body);
            } catch (error) {
              console.error(error);
              window.alert(error);
            }
          }

          // Delete files
          if (to_delete.length) {
            try {
              await this.$api.delete('/files', {
                data: {
                  ...target,
                  filenames: to_delete,
                },
              });
            } catch (error) {
              console.error(error);
              window.alert(error);
            }
          }
        });

      return Promise.all(promises);
    },

    async save() {
      this.saving = true;

      let missing_mandatory_fields = false;

      if (this.phase_data) {
        this.phase_data.forEach((phase) => {
          if (phase.steps) {
            phase.steps.forEach((step) => {
              missing_mandatory_fields =
                missing_mandatory_fields ||
                this.missingMandatoryValues(step.form_fields);
            });
          }
        });
      }

      if (missing_mandatory_fields) {
        window.alert(this.$t('fill_mandatory_fields'));
        this.saving = false;
        return;
      }

      let data = [];
      if (this.phase_data) {
        this.phase_data.forEach((phase) => {
          if (phase.steps) {
            phase.steps.forEach((step) => {
              data = data.concat(
                this.getFormFieldValue(
                  phase.phase_key,
                  step._key,
                  step.form_fields ? step.form_fields : [],
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

      if (this.force_serial_code) {
        serial_data.code = this.force_serial_code;
      }

      const event = {
        event_type: 'SERIAL_CREATED',
        user_key: user,
        user_session_key: this.session_data.session_key,
        timestamp: timestamp(),
        serial_data,
      };

      this.$api.post('event', event).then((resp) => {
        if (resp.status === 200) {
          this.$emit('serialCreated');
          this.saveFiles(resp?.data?.detail?.serial_key).then(() => {
            this.cancel();
            this.saving = false;
          });
        } else if (resp.response?.status === 422) {
          let error_message = 'traceability.errors.EXCEPTION';
          switch (resp.response?.data?.detail?.error_type) {
            case 'SerialNotCreatedError':
              error_message = 'traceability.errors.SERIAL_NEW_ERROR';
              break;
            case 'SerialCodeAlreadyPresent':
              error_message = 'traceability.errors.SERIAL_NEW_ALREADY_PRESENT';
              break;
            default:
              break;
          }

          this.$q.notify({
            message: this.$t(error_message),
            color: 'theme-red',
            timeout: 1500,
            position: 'top',
          });
          this.cancel();
          this.saving = false;
        }
      });
    },
  },
};
</script>
