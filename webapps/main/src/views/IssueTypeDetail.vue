<template>
  <div class="column scroll full-height">
    <template v-if="issue_type">
      <div class="row q-pa-xl">
        <template v-if="!edit_mode">
          <div class="col" v-if="!edit_mode">
            <div class="text-h2 uppercase display highlight">
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
          <div class="column justify-between col-4">
            <q-input
              filled
              stack-label
              hide-bottom-space
              :label="$capitalize($t('name'))"
              v-model="temp_metadata.name">
            </q-input>
            <q-input
              filled
              stack-label
              hide-bottom-space
              :label="$capitalize($t('code'))"
              v-model="temp_metadata.code"
              class="q-mt-md">
            </q-input>
          </div>
          <div class="col-5 q-ml-xl">
            <q-input
              filled
              stack-label
              autogrow
              hide-bottom-space
              :label="$capitalize($t('description'))"
              v-model="temp_metadata.description">
            </q-input>
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
      <div class="row q-px-xl">

        <div class="row">
          <div class="col-4 column">

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

          </div>

          <!-- ISSUE TYPE ICON -->
          <div class="col-8 q-pl-xl">
            <div class="row items-center q-mb-md q-pl-sm">
              <div class="text-h4 text-high q-mr-md">
                {{ $capitalize($t('icon')) }}
              </div>
              <div class="text-low row items-center">
                <q-icon :name="temp_metadata.icon" size="lg" class="q-mr-sm" />
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
            <BaseDialog :show="show_icon_library">
              <div class="surface2 q-pa-md">
                <IconLibrary @choice="(value) => pickIcon(value)" />
              </div>
            </BaseDialog>
          </div>
        </div>
      </div>

    </template>

    <NoDataAlert v-else />
  </div>
</template>

<script>
import IconLibrary from '@/components/IconLibrary.vue'
import NoDataAlert from '@/components/NoDataAlert.vue'
import BaseTooltipIcon from '@/components/BaseTooltipIcon.vue'
import BaseDialog from '@/components/BaseDialog.vue'


export default {

  name: 'IssueTypeDetail',

  components: {
    BaseDialog,
    BaseTooltipIcon,
    NoDataAlert,
    IconLibrary
  },

  props: {
    issue_type: {
      type: Object,
      required: true
    }
  },

  data () {
    return {
      show_icon_library: false,
      edit_mode: false,
      saving: false,
      temp_metadata: {
        name: '',
        code: '',
        active: undefined,
        description: '',
        icon: '',
        critical: undefined,
        // close_within: 0
      }
    }
  },

  methods: {

    setTempData(){
      Object.keys(this.temp_metadata).forEach( key => {
        if (key in this.issue_type) {
          this.temp_metadata[key] = this.issue_type[key]
        }
      })
    },

    pickIcon(value) {
      this.temp_metadata.icon = value
      this.show_icon_library = false
    },

    cancel() {
      this.saving = false
      this.edit_mode = false
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
    },

    showDelete() {
      this.$router.push({
        name: 'issueTypeDelete',
        params: { issue_type_key: this.issue_type._key }
      })
    }
  },

  created() {
    this.setTempData()
  },

  watch: {
    edit_mode() {
      this.setTempData()
    },
    issue_type: {
      handler: 'setTempData',
      deep: true
    }
  }
}
</script>

<style lang="css" scoped>
</style>
