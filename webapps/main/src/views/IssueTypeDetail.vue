<template>
  <div class="full-height column" :class="editMode ? 'q-pa-lg' : 'q-pa-xl'">
    <template v-if="issueType">
      <div class="row q-col-gutter-lg col-auto">
        <template v-if="!editMode">
          <div v-if="!editMode" class="col">
            <div class="text-h2 uppercase display highlight q-mb-sm">
              {{ issueType.name }}
              {{ issueType.code ? '(' + issueType.code + ')' : '' }}
            </div>
            <div style="width: 50%">
              {{ issueType.description || '— No Description —' }}
            </div>
          </div>

          <q-space />

          <BaseTooltipIcon
            icon="mdi-pencil"
            :tooltip="$capitalize($t('edit'))"
            :color="$theme.blue"
            @icon-click="editMode = true"
          >
          </BaseTooltipIcon>

          <BaseTooltipIcon
            icon="mdi-delete"
            :tooltip="$capitalize($t('archive'))"
            :color="$theme.red"
            @icon-click="showDelete"
          >
          </BaseTooltipIcon>
        </template>

        <!-- EDIT ISSUE TYPE METADATA -->
        <template v-else>
          <div class="col-10 row q-col-gutter-lg q-mb-lg">
            <div class="col-3">
              <q-input
                v-model="temp_metadata.code"
                filled
                dense
                stack-label
                hide-bottom-space
                :label="$capitalize($t('code'))"
              >
              </q-input>
            </div>
            <div class="col">
              <q-input
                v-model="temp_metadata.name"
                filled
                dense
                stack-label
                hide-bottom-space
                :label="$capitalize($t('name'))"
              >
              </q-input>
            </div>

            <div class="col-12">
              <q-input
                v-model="temp_metadata.description"
                filled
                dense
                stack-label
                autogrow
                hide-bottom-space
                :label="$capitalize($t('description'))"
              >
              </q-input>
            </div>
          </div>

          <div class="col column q-pl-xl q-gutter-md">
            <q-btn
              size="12px"
              color="theme-blue"
              :loading="saving"
              :label="$t('save')"
              @click="save"
            >
            </q-btn>
            <q-btn
              size="12px"
              color="theme-grey"
              :label="$t('cancel')"
              @click="cancel"
            >
            </q-btn>
          </div>
        </template>
      </div>

      <!-- ISSUE TYPE OPTIONS -->
      <div class="row q-gutter-lg items-center col-auto">
        <!-- ACTIVE -->
        <q-toggle
          v-model="temp_metadata.active"
          :disable="!editMode"
          :label="$capitalize($t('active'))"
        >
        </q-toggle>

        <!-- DEFAULT CRITICAL -->
        <q-toggle
          v-model="temp_metadata.critical"
          :disable="!editMode"
          :label="$capitalize($t('critical'))"
        >
        </q-toggle>

        <!-- CLOSE WITHIN -->
        <!--   <q-input
            filled
            stack-label
            :label="$t('close_within')"
            :disable="!editMode"
            type="number"
            min="0"
            v-model.number="temp_metadata.close_within"
            class="q-mt-lg">
          </q-input>
          <div class="q-mt-md text-low text-italic">
          {{ $t('issue_type_close_within_explainer') }}
          </div> -->

        <!-- ISSUE TYPE ICON -->
        <div class="q-pl-xl">
          <div class="row items-center q-pl-sm">
            <div class="text-h5 text-uppercase weight-bold text-low q-mr-md">
              {{ $t('icon') }}
            </div>
            <div class="text-low row items-center">
              <q-icon :name="temp_metadata.icon" size="md" class="q-mr-sm" />
              <div class="text-body2 text-italic">{{ temp_metadata.icon }}</div>
            </div>
            <q-btn
              v-if="editMode"
              flat
              :label="$t('change')"
              color="theme-blue"
              class="q-ml-xl"
              @click="show_icon_library = true"
            >
            </q-btn>
          </div>

          <BaseDialog :show="show_icon_library" :no-backdrop-dismiss="false">
            <div class="surface2 q-pa-md">
              <IconLibrary @choice="(value) => pickIcon(value)" />
            </div>
          </BaseDialog>
        </div>
      </div>

      <!-- FORM AND PRINT TEMPLATES -->
      <q-tabs
        v-model="tab"
        align="left"
        dense
        indicator-color="theme-blue"
        active-class="text-high weight-bold"
        class="q-mt-lg text-low col-auto"
      >
        <q-tab
          content-class="weight-bold"
          name="form"
          :label="$t('form_title')"
        />
        <q-tab name="prints" :label="$t('print_templates')" />
      </q-tabs>

      <q-card square class="col">
        <q-tab-panels v-model="tab" class="fit">
          <!-- ISSUE TYPE FORM -->
          <q-tab-panel name="form" class="fit surface2 column">
            <FormTemplateEditor
              v-model="temp_metadata.form_template"
              :edit-mode="editMode"
            />
          </q-tab-panel>

          <!-- PRINT TEMPLATES -->
          <q-tab-panel name="prints" class="surface2 column">
            <div class="row col q-col-gutter-md scroll">
              <div
                v-for="(
                  template, index
                ) in temp_metadata.print_templates.filter(
                  ({ trash }) => !trash,
                )"
                :key="template._key"
                class="col-3"
              >
                <PrintTemplateCard
                  :template="template"
                  :allow-delete="editMode"
                  @delete="deleteTemplate(index)"
                />
              </div>
            </div>

            <div class="col-auto">
              <BaseAutocompleteTemplate
                v-if="editMode"
                class="q-px-sm q-mt-md"
                :label="$t('print_template_add')"
                :selected="temp_metadata.print_templates"
                @select="addTemplate"
              />
            </div>
          </q-tab-panel>
        </q-tab-panels>
      </q-card>
    </template>
    <NoDataAlert v-else />
  </div>
</template>

<script>
import { cloneDeep as _cloneDeep } from 'lodash';
import BaseAutocompleteTemplate from '@/components/BaseAutocompleteTemplate.vue';
import BaseDialog from '@/components/BaseDialog.vue';
import BaseTooltipIcon from '@/components/BaseTooltipIcon.vue';
import FormTemplateEditor from '@/components/FormTemplateEditor.vue';
import IconLibrary from '@/components/IconLibrary.vue';
import NoDataAlert from '@/components/NoDataAlert.vue';
import PrintTemplateCard from '@/components/PrintTemplateCard.vue';
import form from '@/mixins/form.js';

export default {
  name: 'IssueTypeDetail',

  components: {
    BaseAutocompleteTemplate,
    BaseDialog,
    BaseTooltipIcon,
    NoDataAlert,
    IconLibrary,
    PrintTemplateCard,
    FormTemplateEditor,
  },

  mixins: [form],

  props: {
    issueType: {
      type: Object,
      required: true,
    },
  },

  data() {
    return {
      show_icon_library: false,
      editMode: false,
      saving: false,
      tab: 'form',
      temp_metadata: {
        name: '',
        code: '',
        active: undefined,
        description: '',
        icon: '',
        critical: undefined,
        form_template: [],
        // close_within: 0
      },
    };
  },

  watch: {
    editMode: 'setTempData',
    issue_type: 'setTempData',
  },

  mounted() {
    this.setTempData();
  },

  methods: {
    setTempData() {
      if (this.issueType) {
        Object.keys(this.temp_metadata).forEach((key) => {
          if (key in this.issueType) {
            this.temp_metadata[key] = _cloneDeep(this.issueType[key]);
          }
        });
      }
    },

    pickIcon(value) {
      this.temp_metadata.icon = value;
      this.show_icon_library = false;
    },

    cancel() {
      this.saving = false;
      this.editMode = false;
      this.$q.notify({
        message: this.$capitalize(this.$t('snackbars.changes_canceled')),
        color: 'theme-grey',
        timeout: 1500,
        position: 'top',
      });
    },

    addTemplate(template) {
      this.temp_metadata.print_templates.push({
        ...template,
        temp: true,
      });
    },

    deleteTemplate(template_index) {
      const template = this.temp_metadata.print_templates[template_index];
      template.temp
        ? this.temp_metadata.print_templates.splice(template_index, 1)
        : (template.trash = true);
    },

    async save() {
      this.saving = true;
      const data = {
        _key: this.issueType._key,
        ...this.temp_metadata,
      };
      await this.$store.dispatch('updateIssueType', data);
      this.saving = false;
      this.editMode = false;
      this.$q.notify({
        message: this.$t('issue_type_update_success'),
        color: 'theme-green',
        timeout: 1500,
        position: 'top',
      });
    },

    showDelete() {
      this.$router.push({
        name: 'issueTypeDelete',
        params: { issueTypeKey: this.issueType._key },
      });
    },
  },
};
</script>
