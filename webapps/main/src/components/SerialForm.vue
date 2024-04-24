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

        <!-- SERIAL LINKS -->
        <q-card-section
          v-if="mode === 'new' && with_links && form_step === 'links'"
          class="column q-gutter-md"
        >
          <!-- "Path" selection (Order, Product, General) -->
          <q-select
            v-if="link_form === null"
            :options="link_form_options"
            filled
            emit-value
            map-options
            visible="false"
            :model-value="link_form"
            :label="$t('serial_new_link_type_label')"
            @update:model-value="updateLinkForm"
          />

          <!-- WORK ORDER -->
          <BaseAutocompleteWorkOrder
            v-if="link_form === 'order'"
            :value="links.work_order"
            :label="$capitalize($t('work_order.long'))"
            @select="(selection) => loadWorkOrder(selection)"
          />

          <!-- PRODUCT -->
          <BaseAutocompleteProduct
            v-if="link_form === 'product'"
            :value="links.product"
            :hint="
              (links.work_order || links.product) && !phase_data
                ? $t('phase.no_phase')
                : null
            "
            key-only
            :label="$capitalize($t('product.label'))"
            @select="(selection) => loadProduct(selection)"
          />

          <!-- PHASE -->
          <q-select
            v-if="phase_data"
            :model-value="links.phase"
            :label="$t('phase.short')"
            filled
            clearable
            :options="phase_data"
            option-label="alias"
            @update:model-value="(selection) => loadPhase(selection)"
          />

          <!-- JOB -->
          <q-select
            v-if="link_form === 'order' && links.phase"
            v-model="links.job"
            :label="$capitalize($t('job.label'))"
            filled
            clearable
            :options="phase_jobs"
          >
            <template #option="scope">
              <JobListItem
                v-bind="scope.itemProps"
                :job-data="scope.opt"
                show-progress
                show-assignee
              />
            </template>
            <template #selected-item="scope">
              <JobListItem :job-data="scope.opt" />
            </template>
          </q-select>

          <template v-if="link_form === 'general'">
            <BaseAutocompleteUser
              v-model="links.user"
              :label="$t('user.label')"
            >
            </BaseAutocompleteUser>
            <BaseAutocompleteOperation
              v-model="links.operation"
              :label="$capitalize($t('operation.label'))"
            >
            </BaseAutocompleteOperation>
          </template>
        </q-card-section>

        <!-- SERIAL DATA -->
        <div v-else key="serial_data">
          <!-- FORM FIELDS -->
          <q-card-section>
            <FormField
              v-for="field in form_fields"
              :key="field._key"
              :field="field"
              :root-path="`/media/serial/${serial?._key}`"
              @update="field.value = $event"
            />
            <FormField
              v-for="field in base_fields"
              :key="field._key"
              :field="field"
              :root-path="`/media/issue/${issue?._key}`"
              @update="field.value = $event"
            />
          </q-card-section>
        </div>

        <!-- FORM ACTIONS -->
        <q-card-section>
          <div class="row q-gutter-md">
            <q-btn
              v-if="mode === 'new' && with_links && form_step === 'links'"
              color="theme-blue"
              :label="$t('next')"
              @click="form_step = 'data'"
            >
            </q-btn>
            <template v-else>
              <q-btn
                v-if="with_links"
                icon="mdi-arrow-left-bold"
                color="theme-blue"
                @click="form_step = 'links'"
              >
              </q-btn>
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
import BaseAutocompleteOperation from '@/components/BaseAutocompleteOperation.vue';
import BaseAutocompleteProduct from '@/components/BaseAutocompleteProduct.vue';
import BaseAutocompleteUser from '@/components/BaseAutocompleteUser.vue';
import BaseAutocompleteWorkOrder from '@/components/BaseAutocompleteWorkOrder.vue';
import BaseDialog from '@/components/BaseDialog.vue';
import FormField from '@/components/FormField.vue';
import JobListItem from '@/components/JobListItem.vue';
import { timestamp } from '@/lib/TimeHandling.js';

export default {
  name: 'SerialForm',

  components: {
    BaseAutocompleteOperation,
    BaseAutocompleteProduct,
    BaseAutocompleteUser,
    BaseAutocompleteWorkOrder,
    BaseDialog,
    JobListItem,
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
    with_links: {
      type: Boolean,
      default: false,
    },
    auto_link_mode: {
      type: String,
      default: undefined,
      validator: (value) => ['work_order', 'product'].includes(value),
    },
    auto_links: {
      type: Object,
      default: null,
    },
  },

  emits: ['close', 'serialCreated'],

  data() {
    return {
      saving: false,
      form_step: 'data',
      form_fields: [],
      base_fields: [],
      confirmed: false,
      link_form: null,
      phase_data: null,
      phase_jobs: null,
      links: {
        product: null,
        operation: null,
        phase: null,
        work_order: null,
        user: null,
        job: null,
      },
    };
  },

  computed: {
    job_data() {
      return this.$store.state.traceability.working_job_data;
    },

    session_data() {
      return this.$store.state.session;
    },

    link_form_options() {
      return [
        {
          value: 'order',
          label: this.$t('work_order.long'),
        },
        {
          value: 'product',
          label: this.$t('product.label'),
        },
        {
          value: 'general',
          label: this.$t('general'),
        },
      ];
    },
  },

  watch: {
    show: {
      handler() {
        this.initFormData();
        this.initLinks();
      },
    },
    phase_data() {
      // The new list of phases will not contain the selected phase, so reset it
      this.links.phase = null;
    },
  },

  created() {
    this.initBaseFields();
    this.initFormData();
    this.initLinks();
  },

  methods: {
    updateLinkForm(value) {
      this.link_form = value;
      this.initLinks();
    },

    initLinks() {
      // Inser links step if required
      if (this.mode == 'new' && this.with_links) {
        this.form_step = 'links';
      }

      // Reset links
      if (this.with_links) {
        Object.keys(this.links).forEach((l) => (this.links[l] = null));
        this.phase_data = null;
        this.phase_jobs = null;
      }

      // Set auto links if required
      if (this.auto_link_mode == 'work_order' && this.auto_links.work_order) {
        this.link_form = 'order';
        this.loadWorkOrder(this.auto_links.work_order);
      }

      if (this.auto_link_mode == 'product') {
        this.link_form = 'product';
      }

      if (this.auto_link_mode == 'work_session' && this.auto_links) {
        Object.entries(this.auto_links).forEach(([k, v]) => {
          this.links[k] = { _key: v };
        });
      }
    },

    initFormData() {
      const form_template = this.form_template ?? [];

      const use_clean_form = this.mode === 'new';
      if (use_clean_form) {
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

    async loadWorkOrder(wo) {
      // Set work order data and initialize Phase options to select from
      this.links.work_order = wo;
      this.links.product = { _key: wo.product_key };

      let params = new URLSearchParams();
      this.links.work_order.phase_sequence.forEach((pk) =>
        params.append('phase_key', pk),
      );

      const { data } = await this.$api.get('phase', { params });
      this.phase_data = data;
    },

    async initBaseFields() {
      const { data: fields } = await this.$api.get('serial-field');
      this.base_fields = fields;
    },

    async loadProduct(product_key) {
      // To avoid loading in advance a lot of unnecessary product data, the product list contains limited information.
      // So, it is necessary to fetch the full product data first and then load the phases options.
      const { data: product } = await this.$api.get(`product/${product_key}`);
      this.links.product = product;

      if (!product.process_phases) {
        return;
      }

      const params = new URLSearchParams();
      product.process_phases.forEach((phaseKey) =>
        params.append('phase_key', phaseKey),
      );
      const { data: phase } = await this.$api.get('phase', { params });
      this.phase_data = phase;
    },

    async loadPhase(phase_data) {
      this.links.phase = phase_data;
      this.links.operation = { _key: phase_data.operation_key };

      // Phase link exists for both order and product mode. Load jobs only in order mode
      if (this.link_form !== 'order') {
        return;
      }

      const { data } = await this.$api.get('job', {
        params: {
          work_order_key: this.links.work_order._key,
          phase_key: this.links.phase._key,
        },
      });
      this.phase_jobs = data.detail;
    },

    cancel() {
      this.initFormData();
      this.initLinks();
      this.form_step = 'links';
      this.link_form = null;
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

    async saveFiles(serial_key) {
      const promises = this.form_fields
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

      const message =
        this.mode === 'new' ? 'serial_new_success' : 'serial_update_success';
      const { data } = await this.$api.post('event', event);
      const serial_key =
        this.mode === 'new' ? data.detail.serial_key : serial_data._key;
      await this.saveFiles(serial_key);

      // If from work session, fetch serials directly, otherwise signal the parent component to do so
      if (!this.with_links) {
        await this.$store.dispatch('getSerials', {
          work_order_key: this.job_data.wo_key,
        });
      } else {
        this.$emit('serialCreated');
      }
      this.cancel();
      this.saving = false;
      this.$q.notify({
        message: this.$t(message),
        color: 'theme-orange',
        timeout: 1500,
        position: 'top',
      });
    },
  },
};
</script>
