<template>
  <div class="full-height column" :class="edit_mode ? 'q-pa-lg' : 'q-pa-xl'">
    <template v-if="issue_type">
      <div class="row q-col-gutter-lg col-auto">

        <template v-if="!edit_mode">
          <div class="col" v-if="!edit_mode">
            <div class="text-h2 uppercase display highlight q-mb-sm">
              {{ issue_type.name }} {{ issue_type.code ? '(' + issue_type.code + ')' : ''}}
            </div>
            <div style="width: 50%">
              {{ issue_type.description || '— No Description —' }}
            </div>
          </div>

          <q-space />

          <BaseTooltipIcon
            icon="mdi-pencil"
            :tooltip="$capitalize($t('edit'))"
            :color="$theme.blue"
            @iconClick="edit_mode=true">
          </BaseTooltipIcon>

          <BaseTooltipIcon
            icon="mdi-delete"
            :tooltip="$capitalize($t('archive'))"
            :color="$theme.red"
            @iconClick="showDelete">
          </BaseTooltipIcon>
        </template>

        <!-- EDIT ISSUE TYPE METADATA -->
        <template v-else>
          <div class="col-10 row q-col-gutter-lg q-mb-lg">
            <div class="col-3">
              <q-input
                filled
                dense
                stack-label
                hide-bottom-space
                :label="$capitalize($t('code'))"
                v-model="temp_metadata.code">
              </q-input>
            </div>
            <div class="col">
              <q-input
                filled
                dense
                stack-label
                hide-bottom-space
                :label="$capitalize($t('name'))"
                v-model="temp_metadata.name">
              </q-input>
            </div>

            <div class="col-12">
              <q-input
                filled
                dense
                stack-label
                autogrow
                hide-bottom-space
                :label="$capitalize($t('description'))"
                v-model="temp_metadata.description">
              </q-input>
            </div>

          </div>

          <div class="col column q-pl-xl q-gutter-md">
            <q-btn
              size="12px"
              color="theme-blue"
              @click="save"
              :loading="saving"
              :label="$t('save')">
            </q-btn>
            <q-btn
              size="12px"
              color="theme-grey"
              @click="cancel"
              :label="$t('cancel')">
            </q-btn>
          </div>
        </template>
      </div>


      <!-- ISSUE TYPE OPTIONS -->
      <div class="row q-gutter-lg items-center col-auto">

        <!-- ACTIVE -->
        <q-toggle
          :disable="!edit_mode"
          :label="$capitalize($t('active'))"
          v-model="temp_metadata.active">
        </q-toggle>

        <!-- DEFAULT CRITICAL -->
        <q-toggle
          :disable="!edit_mode"
          :label="$capitalize($t('critical'))"
          v-model="temp_metadata.critical">
        </q-toggle>

        <!-- CLOSE WITHIN -->
        <!--   <q-input
            filled
            stack-label
            :label="$t('close_within')"
            :disable="!edit_mode"
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
              v-if="edit_mode"
              flat
              :label="$t('change')"
              @click="show_icon_library = true"
              color="theme-blue"
              class="q-ml-xl">
            </q-btn>
          </div>

          <BaseDialog :show="show_icon_library" :no-backdrop-dismiss="false">
            <div class="surface2 q-pa-md">
              <IconLibrary @choice="(value) => pickIcon(value)" />
            </div>
          </BaseDialog>

        </div>
      </div>

      <!-- ISSUE TYPE FORM -->
      <div class="text-h4 text-uppercase weight-bold q-mt-lg q-mb-sm col-auto">
        {{ $t('form_title')}}
      </div>

      <div
        v-if="!temp_metadata.form_template.length"
        class="q-mt-md text-italic">
        {{ $t('field_none') }}
      </div>

      <div v-else class="col scroll" id="issue-type-fields">

        <div
          class="row items-center q-col-gutter-lg q-py-sm"
          v-for="(field, index) in temp_metadata.form_template"
          :key="field._key">

          <div class="col-auto">
            <q-icon
              v-if="edit_mode"
              name="mdi-drag-horizontal-variant"
              class="q-mr-sm dragme"
              size="sm">
            </q-icon>
            <q-icon
              :name="getFieldIcon(field.type)"
              size="sm">
            </q-icon>
          </div>

          <!-- Label -->
          <div class="col">
            <q-input
              stack-label
              filled
              dense
              autogrow
              :readonly="!edit_mode"
              :label="$t('label')"
              v-model="field.label">
            </q-input>
          </div>

          <!-- Hint -->
          <div class="col">
            <q-input
              stack-label
              filled
              dense
              autogrow
              :readonly="!edit_mode"
              :label="$t('hint')"
              v-model="field.hint">
            </q-input>
          </div>

          <div class="col-auto">

          </div>

          <div class="col-auto">
            <q-btn
              v-if="edit_mode"
              round flat
              icon="mdi-close"
              @click="deleteField(index)">
            </q-btn>
          </div>
          <!-- TODO: default value and hidden -->
        </div>

        <!-- BUTTON: Add field -->
      </div>

      <div class="row">
        <q-btn
          v-if="edit_mode"
          size="sm"
          color="theme-blue"
          icon="mdi-plus"
          :label="$t('field_add')"
          @click="show_field_dialog=true"
          class="q-mt-lg">
        </q-btn>
      </div>



      <BaseDialog
        :show="show_field_dialog"
        :no-backdrop-dismiss="false"
        @close="show_field_dialog=false">
        <!-- Field picker -->
        <FormFieldSearch
          @select="addField"
          :exclude-keys="selected_field_keys">
        </FormFieldSearch>
      </BaseDialog>

    </template>

    <NoDataAlert v-else />
  </div>
</template>

<script>
import IconLibrary from '@/components/IconLibrary.vue'
import NoDataAlert from '@/components/NoDataAlert.vue'
import BaseTooltipIcon from '@/components/BaseTooltipIcon.vue'
import BaseDialog from '@/components/BaseDialog.vue'
import FormFieldSearch from '@/components/FormFieldSearch.vue'
import form from '@/mixins/form.js'
import { cloneDeep as _cloneDeep } from 'lodash'
import Sortable from 'sortablejs'


export default {

  name: 'IssueTypeDetail',

  components: {
    BaseDialog,
    BaseTooltipIcon,
    FormFieldSearch,
    NoDataAlert,
    IconLibrary
  },

  mixins: [form],

  props: {
    issue_type: {
      type: Object,
      required: true
    }
  },

  data () {
    return {
      show_icon_library: false,
      show_field_dialog: false,
      edit_mode: false,
      saving: false,
      temp_metadata: {
        name: '',
        code: '',
        active: undefined,
        description: '',
        icon: '',
        critical: undefined,
        form_template: []
        // close_within: 0
      },
    }
  },

  computed: {
    selected_field_keys() {
      return this.temp_metadata.form_template.map(f => f._key)
    }
  },

  methods: {

    setTempData(){
      if (this.issue_type) {
        Object.keys(this.temp_metadata).forEach( key => {
          if (key in this.issue_type) {
            this.temp_metadata[key] = _cloneDeep(this.issue_type[key])
          }
        })
      }
    },

    pickIcon(value) {
      this.temp_metadata.icon = value
      this.show_icon_library = false
    },

    cancel() {
      this.saving = false
      this.edit_mode = false
      this.$q.notify({
        message: this.$capitalize(this.$t('snackbars.changes_canceled')),
        color: 'theme-grey',
        timeout: 1500,
        position: 'top'
      })
    },

    async save() {
      this.saving = true
      const data = {
        _key: this.issue_type._key,
        ...this.temp_metadata
      }
      await this.$store.dispatch('updateIssueType', data)
      this.saving = false
      this.edit_mode = false
      this.$q.notify({
        message: this.$t('issue_type_update_success'),
        color: 'theme-green',
        timeout: 1500,
        position: 'top'
      })
    },

    showDelete() {
      this.$router.push({
        name: 'issueTypeDelete',
        params: { issue_type_key: this.issue_type._key }
      })
    },

    addField(field_data) {
      this.temp_metadata.form_template.push({
        _key: field_data._key,
        type: field_data.type,
        label: field_data.default_label,
        hint: field_data.default_hint,
        // multiple: false,
        // required: false
      })
      this.show_field_dialog = false
    },

    deleteField(index) {
      this.temp_metadata.form_template.splice(index, 1)
    },

    initSortable() {
      const _self = this
      let container = document.querySelector("#issue-type-fields")
      if (container) {
        Sortable.create(container, {
          ..._self.$store.state.drag_options,
          handle: ".dragme",
          onStart: () => _self.dragging = true,
          // use onEnd event provided by SortableJs library
          onEnd: ({ newIndex, oldIndex }) => {
            _self.dragging = false
            const moved = _self.temp_metadata.form_template.splice(oldIndex, 1)[0]
            _self.temp_metadata.form_template.splice(newIndex, 0, moved)
          }
        })
      }
    }
  },

  mounted() {
    this.setTempData()
  },

  watch: {
    edit_mode() {
      this.setTempData()
      this.initSortable()
    },
    issue_type: 'setTempData'
  }
}
</script>

<style lang="css" scoped>
</style>
