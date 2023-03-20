<template>
  <div class="column full-height">
    <template v-if="issue_type">
      <div class="row q-pa-lg q-ma-md">
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

        <template v-else>
          <div class="column justify-between col-4">
            <q-input
              hide-bottom-space
              :label="$capitalize($t('name'))"
              v-model="temp_metadata.name">
            </q-input>
            <q-input
              hide-bottom-space
              :label="$capitalize($t('code'))"
              v-model="temp_metadata.code">
            </q-input>
          </div>
          <div class="col-5 q-ml-xl">
            <q-input
              type="textarea"
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

      <q-separator />

      <div class="col scroll">
        <q-input v-model="temp_metadata.close_within" />
        <q-toggle v-model="temp_metadata.critical" />
        <IconLibrary @choice="value => temp_metadata.icon = value"/>
      </div>
    </template>

    <NoDataAlert v-else />
  </div>
</template>

<script>
import IconLibrary from '@/components/IconLibrary.vue'
import NoDataAlert from '@/components/NoDataAlert.vue'
import BaseTooltipIcon from '@/components/BaseTooltipIcon.vue'

export default {

  name: 'OperationDetail',

  components: {
    BaseTooltipIcon,
    NoDataAlert
  },

  props: {
    issue_type: {
      type: Object,
      required: true
    }
  },

  data () {
    return {
      edit_mode: false,
      saving: false,
      temp_metadata: {
        name: '',
        code: '',
        description: '',
        icon: '',
        critical: '',
        close_within: 0
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

    cancel() {
      this.saving = false
      this.edit_mode = false
    },

    async save() {
      this.saving = true
      const data = {
        key: this.issue_type._key,
        update: this.temp_metadata
      }
      await this.$store.dispatch('updateIssueType', data)
      this.saving = false
      this.edit_mode = false
    },

    // showDelete() {
    //   if (this.products_using_operation.length) {
    //     const product_codes = this.products_using_operation.map( o => o.code )
    //     window.alert(c(this.$tc('operation.alerts.op_in_use') + ": " +  product_codes))
    //   }
    //   else {
    //     this.$router.push({
    //       name: 'operationDelete',
    //       params: { operation_key: this.operation._key }
    //     })
    //   }
    // },
  },

  watch: {
    edit_mode() {
      this.setTempData()
    }
  }
}
</script>

<style lang="css" scoped>
</style>
