<template>
  <div class="q-pa-lg">
    <div class="row justify-between items-start">

      <div class="col-6 q-gutter-md">
      <!-- Field type -->
        <q-select
          filled
          :disable="!edit_mode"
          :label="$t('type')"
          :options="field_types"
          v-model="temp_data.type"
          emit-value
          map-options>
          <template #option="scope">
            <q-item v-bind="scope.itemProps">
              <q-item-section avatar>
                <q-icon :name="scope.opt.icon" />
              </q-item-section>
              <q-item-section>
                <q-item-label>
                  {{ scope.opt.label }}
                </q-item-label>
              </q-item-section>
            </q-item>
          </template>
        </q-select>


        <!-- Field default name -->
        <q-input
          filled
          :disable="!edit_mode"
          :label="$t('name')"
          stack-label
          v-model="temp_data.name">
        </q-input>

        <!-- Field default Label -->
        <q-input
          filled
          :label="$t('label')"
          :disable="!edit_mode"
          stack-label
          v-model="temp_data.default_label">
        </q-input>

        <!-- Field default hint -->
        <q-input
          filled
          :disable="!edit_mode"
          :label="$t('hint')"
          stack-label
          autogrow
          v-model="temp_data.default_hint">
        </q-input>


        <template v-if="field.type == 'choice'">
          <!-- SHOW NUMBER OF VALUES -->
          {{ original_values.length }}
          <!-- Link to modal to view/update values -->
          <!-- In modal place a disclaimer: changes will not update data already recorded -->
        </template>
      </div>

      <!-- ACTION BUTTONS -->
      <div class="col-auto">
        <template v-if="!edit_mode">
          <BaseTooltipIcon
            icon="mdi-pencil"
            :tooltip="$capitalize($t('edit'))"
            :color="$theme.blue"
            @iconClick="edit_mode=true">
          </BaseTooltipIcon>

          <BaseTooltipIcon
            icon="mdi-delete"
            :tooltip="$capitalize($t('delete'))"
            :color="$theme.red"
            @iconClick="show_delete = true">
          </BaseTooltipIcon>
        </template>

        <template v-else>
          <div class="col q-gutter-md">
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
    </div>
    <!-- List values if necessary -->
  </div>
</template>

<script>
import form from '@/mixins/form.js'
import BaseTooltipIcon from '@/components/BaseTooltipIcon.vue'

export default {

  name: 'FormFieldDetail',

  mixins: [form],

  components: {
    BaseTooltipIcon
  },

  props: {
    field: Object,
  },

  data () {
    return {
      temp_data: {
        type: null,
        name: null,
        default_label: null,
        default_hint: null
      },
      original_values: [],
      temp_values: [],
      show_delete: false,
      edit_mode: false
    }
  },

  methods: {
    initTempData() {
      Object.keys(this.temp_data).forEach(k => this.temp_data[k] = this.field[k])
      if (this.field.type == 'choice') {
        this.$api.get('list', { params: { field_key: this.field._key }})
        .then( resp => this.original_values = resp.data )
      }
    },

    save() {
      this.$api.put(`field/${this.field._key}`, { ...this.field, ...this.temp_data })
      .then(() => {
        this.$emit('saved')
        this.edit_mode = false
      })
    },

    cancel() {
      this.edit_mode = false
      this.initTempData()
    }
  },

  mounted() {
    this.initTempData()
  },

  watch: {
    field: {
      handler() {
        this.initTempData()
        this.edit_mode = false
      }
    }
  }
}
</script>

<style lang="css" scoped>
</style>
