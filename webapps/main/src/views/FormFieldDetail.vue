<template>
  <div class="q-pa-lg column full-height">
    <div class="row justify-between items-start">

      <div class="col-10 row q-col-gutter-md">
      <!-- Field type -->
        <div class="col-4">
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
        </div>


        <!-- Field default name -->
        <div class="col-4">
          <q-input
            filled
            :disable="!edit_mode"
            :label="$t('name')"
            stack-label
            v-model="temp_data.name">
          </q-input>
        </div>

        <!-- Field default Label -->
        <div class="col-4">
          <q-input
            filled
            :label="$t('label')"
            :disable="!edit_mode"
            stack-label
            v-model="temp_data.default_label">
          </q-input>
        </div>

        <!-- Field default hint -->
        <div class="col-12">
          <q-input
            filled
            :disable="!edit_mode"
            :label="$t('hint')"
            stack-label
            autogrow
            v-model="temp_data.default_hint">
          </q-input>
        </div>
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
          <div class="col column q-gutter-md">
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
    <template v-if="field.type == 'choice'">
      <div class="row full-width items-center q-col-gutter-md q-my-md q-px-xs">
        <div class="text-h3 col-2 q-px-none">
          {{ $t('value', 2) }}
        </div>
        <q-space />

        <template v-if="edit_mode">
          <div class="col-auto">
            <q-btn
              size="10px"
              icon="mdi-plus"
              color="theme-blue"
              :label="$t('add')"
              @click="addListItem">
            </q-btn>
          </div>

          <div class="col-auto" v-if="selected_items.length">
            <q-btn
              size="10px"
              icon="mdi-delete"
              color="theme-red"
              :label="$t('delete')"
              @click="deleteListItems">
            </q-btn>
          </div>
        </template>

        <q-input
          filled
          dense
          :label="$capitalize($t('search'))"
          debounce="500"
          v-model="list_search">
          <template #append>
            <q-icon name="mdi-magnify" />
          </template>
        </q-input>
      </div>

      <div class="col">
        <q-table
          :columns="list_cols"
          :rows="shown_list_values"
          color="primary"
          id="list-values"
          class="full-height"
          table-class="text-high "
          card-class="surface2 shadow-2"
          flat
          dense
          square
          virtual-scroll
          separator="none"
          hide-bottom
          :selection="edit_mode ? 'multiple' : 'none'"
          v-model:selected="selected_items"
          :rows-per-page-options="[0]"
          row-key="index">
          <template #body-cell="props">
            <q-td
              :props="props"
              class="q-pl-none">
              <q-input
                filled
                dense
                :disable="!edit_mode"
                v-model="temp_values[props.row.index][props.col.field]"
                :class="getItemClasses(props)">
              </q-input>
            </q-td>
          </template>
        </q-table>
      </div>

    </template>
  </div>
</template>

<script>
import form from '@/mixins/form.js'
import BaseActionCard from '@/components/BaseActionCard.vue'
import BaseDialog from '@/components/BaseDialog.vue'
import BaseTooltipIcon from '@/components/BaseTooltipIcon.vue'
import multiMatch from '@/lib/MultiFieldSearch.js'

export default {

  name: 'FormFieldDetail',

  mixins: [form],

  components: {
    BaseActionCard,
    BaseDialog,
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
      saving: false,
      original_values: [],
      temp_values: [],
      show_delete: false,
      edit_mode: false,
      list_search: null,
      selected_items: []
    }
  },

  computed: {
    list_cols() {
      return [
        {
          name: 'value',
          field: 'value',
          label: this.$t('value'),
          align: 'left',
          style: { "white-space": 'pre-wrap'}
        },
        {
          name: 'ext_key',
          field: 'ext_key',
          label: this.$t('ext_key'),
          style: 'width: 25%',
          align: 'left'
        },
      ]
    },

    shown_list_values() {
      // Map must happen before the filter so the index is preserved, otherwise the same index would refer to different records depending on the filter
      return this.temp_values.map( (row, index) => ({ ...row, index })).filter(
        row => multiMatch(this.list_search, row, ['ext_key', 'value'])
      )
    },

    new_or_updated_items() {
      // This is the list of values to send to the POST endpoint
      return this.temp_values.filter(row => row.new || (!row.delete && row.touched.length))
    },

    deleted_items() {
      // This is the list of values to send to the DELETE endpoint
      return this.temp_values.filter(row => row.delete)
    }
  },

  methods: {

    initTempFieldData() {
      Object.keys(this.temp_data).forEach(k => this.temp_data[k] = this.field[k])
    },

    initTempValues() {
      this.temp_values = this.original_values.map(row => ({
        ...row,
        touched: [],
        new: false,
        delete: false
      }))
    },

    getItemClasses(props) {
      return props.row.delete ? 'bg-red-backdrop text-strike'
        : props.row.new ? 'bg-green-backdrop text-italic'
        : props.value != this.original_values.find(v => v._key == props.row._key)[props.col.field] ? 'bg-orange-backdrop'
        : ''
    },

    save() {
      this.saving = true
      const calls = [
        this.$api.put(`field/${this.field._key}`, { ...this.field, ...this.temp_data }),
        this.$api.post(`list/${this.field._key}`, this.new_or_updated_items)
      ]

      if (this.deleted_items.length) {
        // Need to use URLSearchParams to avoid square brackets in the query param name (e.g. ?value_key[]=XXX -> ?value_key=XXX)
        let params = new URLSearchParams()
        this.deleted_items.forEach(item => params.append('value_key', item._key))
        calls.push(this.$api.delete(`list/${this.field._key}`, { params }))
      }

      this.$axios.all(calls).then(() => {
        this.$emit('saved')
        this.saving = false
        this.edit_mode = false
        if (this.field.type == 'choice') this.loadListValues()
      })
    },

    cancel() {
      this.selected_items = []
      this.initTempFieldData()
      this.initTempValues()
      this.edit_mode = false
    },

    loadListValues() {
      this.$api.get('list', { params: { field_key: this.field._key }})
      .then( resp => {
        this.original_values = resp.data
        this.initTempValues()
      })
    },

    addListItem() {
      this.temp_values.unshift({
        field_key: this.field._key,
        ext_key: null,
        value: this.$t('new'),
        new: true,
        touched: ['ext_key', 'value'],
        delete: false
      })
    },

    deleteListItems() {
      // Flag for deletion original values, remove temporary ones
      this.selected_items.forEach(i => this.temp_values[i.index].delete = true)
      this.temp_values = this.temp_values.filter(v => !(v.delete && v.new))
      this.selected_items = []
    },

    initListEditData() {
      this.edit_list = {
        show: false,
        index: null,
        field: null
      }
    }
  },

  mounted() {
    this.initTempFieldData()
    if (this.field.type == 'choice') this.loadListValues()
  },

  watch: {
    field: {
      handler() {
        this.initTempFieldData()
        if (this.field.type == 'choice') this.loadListValues()
        this.edit_mode = false
      }
    }
  }
}
</script>

<style lang="sass">
#list-values
  td::before
    // remove hover highlight
    background-color: transparent

  .q-table--dense .q-table td:first-child
  thead tr:first-child th /* bg color is important for th; just specify one */
    background-color: var(--surface-2)
    padding-top: 8px
    padding-bottom: 8px
    border-bottom: 1px solid rgba(255, 255, 255, .3)

  thead
    position: sticky
    z-index: 1
    top: 0

  tbody tr:first-child td
    padding-top: 8px !important
</style>
