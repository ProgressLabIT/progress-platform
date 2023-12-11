<template>
  <BaseDialog :show="show">
    <q-card
      square
      class="surface1 q-pa-md"
      style="min-width: 600px; max-width: 800px"
    >
      <q-form ref="issue-form">
        <!-- FORM TITLE -->
        <q-card-section>
          <div class="row justify-between items-center">
            <div class="text-h2 display highlight text-center">
              <template v-if="mode == 'new'">
                {{ $t('issue_new_title') }}
              </template>
              <template v-else>
                {{ $t('issue_update_title') }}
              </template>
            </div>
          </div>
        </q-card-section>

        <!-- FORM BODY -->

        <!-- ISSUE LINKS -->
        <q-card-section
          v-if="mode == 'new' && with_links && form_step == 'links'"
          class="column q-gutter-md"
        >
          <!-- "Path" selection (Order, Product, General) -->
          <q-select
            :options="link_form_options"
            filled
            clearable
            emit-value
            map-options
            :model-value="link_form"
            @update:model-value="updateLinkForm"
            :label="$t('issue_new_link_type_label')"
          >
          </q-select>

          <!-- WORK ORDER -->
          <BaseAutocompleteWorkOrder
            v-if="link_form == 'order'"
            :value="links.work_order"
            :label="$capitalize($t('work_order.long'))"
            @select="(selection) => loadWorkOrder(selection)"
          >
          </BaseAutocompleteWorkOrder>

          <!-- PRODUCT -->
          <BaseAutocompleteProduct
            v-if="link_form == 'product'"
            :value="links.product"
            :hint="
              (links.work_order || links.product) && !phase_data
                ? $t('phase.no_phase')
                : null
            "
            key_only
            :label="$capitalize($t('product.label'))"
            @select="(selection) => loadProduct(selection)"
          >
          </BaseAutocompleteProduct>

          <!-- PHASE -->
          <q-select
            v-if="phase_data"
            :model-value="links.phase"
            @update:model-value="(selection) => loadPhase(selection)"
            :label="$t('phase.short')"
            filled
            clearable
            :options="phase_data"
            option-label="alias"
          >
          </q-select>

          <!-- JOB -->
          <q-select
            v-if="link_form == 'order' && links.phase"
            v-model="links.job"
            :label="$capitalize($t('job.label'))"
            filled
            clearable
            :options="phase_jobs"
          >
            <template #option="scope">
              <JobListItem
                v-bind="scope.itemProps"
                :job_data="scope.opt"
                show_progress
                show_assignee
              />
            </template>
            <template #selected-item="scope">
              <JobListItem :job_data="scope.opt" />
            </template>
          </q-select>

          <template v-if="link_form == 'general'">
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

        <!-- ISSUE DATA -->
        <div v-else key="issue_data">
          <!-- ISSUE TYPE SELECTION -->
          <q-card-section>
            <BaseAutocompleteIssueType
              :value="issue_type"
              @select="(value) => setIssueType(value)"
            />
          </q-card-section>

          <!-- FORM FIELDS -->
          <q-card-section>
            <template v-if="issue_type">
              <FormField
                v-for="field in form_fields"
                :key="field._key"
                :field="field"
                :root-path="`/media/issue/${issue?._key}`"
                @update="field.value = $event"
              />
            </template>
          </q-card-section>
        </div>

        <!-- FORM ACTIONS -->
        <q-card-section>
          <div class="row q-gutter-md">
            <q-btn
              v-if="mode == 'new' && with_links && form_step == 'links'"
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
                v-if="!critical_only"
                color="theme-orange"
                :label="$t('save')"
                @click="
                  () => {
                    critical = false;
                    save();
                  }
                "
                :loading="saving"
              >
              </q-btn>
              <q-btn
                color="theme-red"
                @click="
                  () => {
                    critical = true;
                    save();
                  }
                "
              >
                {{ $t('save') }} {{ $t('critical') }}
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
import BaseAutocompleteIssueType from '@/components/BaseAutocompleteIssueType.vue';
import BaseAutocompleteOperation from '@/components/BaseAutocompleteOperation.vue';
import BaseAutocompleteProduct from '@/components/BaseAutocompleteProduct.vue';
import BaseAutocompleteUser from '@/components/BaseAutocompleteUser.vue';
import BaseAutocompleteWorkOrder from '@/components/BaseAutocompleteWorkOrder.vue';
import BaseDialog from '@/components/BaseDialog.vue';
import FormField from '@/components/FormField.vue';
import JobListItem from '@/components/JobListItem.vue';
import { timestamp } from '@/lib/TimeHandling.js';

export default {
  name: 'IssueForm',

  components: {
    BaseAutocompleteIssueType,
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
    issue: {
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
      validator: (value) => ['work_order', 'work_session'].includes(value),
    },
    auto_links: {
      type: Object,
      default: null,
    },
  },

  emits: ['close', 'issueCreated'],

  data() {
    return {
      critical_only: false,
      saving: false,
      issue_type: null,
      form_step: 'data',
      form_fields: [],
      confirmed: false,
      critical: false,
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

  methods: {
    updateLinkForm(value) {
      this.link_form = value;
      this.initLinks();
    },

    initLinks() {
      // Inser links step if required
      if (this.mode == 'new' && this.with_links) this.form_step = 'links';

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

      if (this.auto_link_mode == 'work_session' && this.auto_links) {
        Object.entries(this.auto_links).forEach(([k, v]) => {
          this.links[k] = { _key: v };
        });
      }
    },

    initFormData() {
      const form_template = this.issue_type?.form_template ?? [];

      const use_clean_form =
        this.mode === 'new' ||
        this.issue_type?._key !== this.issue.issue_type_key;
      if (use_clean_form) {
        // Use fields from issue type template adding empty value
        // If no template, force null, otherwise `undefined` will not be included in the api body and the issue data will not be updated
        this.form_fields = form_template.map((field) => ({
          ...field,
          value: null,
        }));
        return;
      }

      this.form_fields = form_template.map((field) => ({
        ...field,
        value: this.issue.data.find(
          ({ form_field_key }) => form_field_key === field._key,
        )?.value,
      }));
    },

    initIssueType() {
      // Fetch issue type data if editing an existing issue
      this.issue_type =
        this.issue?.issue_type_key != null
          ? this.$store.getters.getIssueType(this.issue.issue_type_key)
          : null;
    },

    setIssueType(value) {
      this.issue_type = value;
      if (value?.critical) {
        this.critical_only = true;
      } else {
        this.critical_only = false;
      }
    },

    loadWorkOrder(wo) {
      // Set work order data and initialize Phase options to select from
      this.links.work_order = wo;
      this.links.product = { _key: wo.product_key };

      let params = new URLSearchParams();
      this.links.work_order.phase_sequence.forEach((pk) =>
        params.append('phase_key', pk),
      );

      this.$api
        .get('phase', { params })
        .then((resp) => (this.phase_data = resp.data));
    },

    loadProduct(product_key) {
      // To avoid loading in advance a lot of unnecessary product data, the product list contains limited information. Thus it is necessary to fetch the full product data first and then load the phases options.
      this.$api.get(`product/${product_key}`).then((resp) => {
        this.links.product = resp.data;
        if (this.product.process_phases) {
          let params = new URLSearchParams();
          this.links.product.process_phases.forEach((p) =>
            params.append('phase_key', p),
          );
          this.$api
            .get('phase', { params })
            .then((resp) => (this.phase_data = resp.data));
        }
      });
    },

    loadPhase(phase_data) {
      this.links.phase = phase_data;
      this.links.operation = { _key: phase_data.operation_key };
      // Phase link exists for both order and product mode. Load jobs only in order mode
      if (this.link_form == 'order') {
        this.$api
          .get('job', {
            params: {
              work_order_key: this.links.work_order._key,
              phase_key: this.links.phase._key,
            },
          })
          .then((resp) => (this.phase_jobs = resp.data.detail));
      }
    },

    cancel() {
      this.initIssueType();
      this.initFormData();
      this.initLinks();
      this.form_step = 'links';
      this.link_form = null;
      this.critical_only = false;
      this.$emit('close');
    },

    async saveFiles(issue_key) {
      const promises = this.form_fields
        .filter(({ type }) => type === 'files')
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
            bucket: 'issue',
            object_key: issue_key,
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

      const issue_data = {
        issue_type_key: this.issue_type?._key || null,
        critical: this.critical,
        data: this.form_fields.map((field) => ({
          form_field_key: field._key,
          custom_field_key: field.custom_field_key,
          value:
            field.type === 'files'
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
        issue_data.created_by = `User/${user}`; // temporarily hardcoding DB id
        issue_data.close_within = this.issue_type?.close_within ?? 0;

        // Map links to list of objects, including only populated properties
        const links = [];
        Object.entries(this.links).forEach(([key, value]) => {
          if (value) {
            links.push({ type: key, key: value._key });
          }
        });
        issue_data.linked_to = links;
      } else {
        issue_data._key = this.issue._key;
      }

      const event = {
        event_type: this.mode === 'new' ? 'ISSUE_CREATED' : 'ISSUE_UPDATED',
        user_key: user,
        user_session_key: this.session_data.session_key,
        timestamp: timestamp(),
        issue_data,
      };

      const message =
        this.mode === 'new' ? 'issue_new_success' : 'issue_update_success';
      const { data } = await this.$api.post('event', event);
      const issue_key =
        this.mode === 'new' ? data.detail.issue_key : issue_data._key;
      await this.saveFiles(issue_key);

      // If from work session, fetch issues directly, otherwise signal the parent component to do so
      if (!this.with_links) {
        await this.$store.dispatch('getIssues', {
          work_order_key: this.job_data.wo_key,
        });
      } else {
        this.$emit('issueCreated');
      }
      this.cancel();
      this.saving = false;
      this.$q.notify({
        message: this.$t(message),
        color: this.critical ? 'theme-red' : 'theme-orange',
        timeout: 1500,
        position: 'top',
      });
    },
  },

  created() {
    this.initIssueType();
    this.initFormData();
    this.initLinks();
  },

  watch: {
    issue_type: {
      deep: true,
      handler: 'initFormData',
    },
    show: {
      handler() {
        this.initFormData();
        this.initLinks();
      },
    },
  },
};
</script>

<style lang="sass" scoped></style>
