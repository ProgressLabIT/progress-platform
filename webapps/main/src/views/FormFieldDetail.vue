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
          class="full-height sticky-header-table"
          table-class="text-high "
          card-class="surface2"
          bordered
          flat
          dense
          square
          virtual-scroll
          separator="cell"
          hide-bottom
          :selection="edit_mode ? 'multiple' : 'none'"
          v-model:selected="selected_items"
          :rows-per-page-options="[0]"
          row-key="_key">
          <template #body-cell="props" v-if="edit_mode">
            <q-td
              :props="props"
              @click="openEditDialog(props)"
              :class="{ 'bg-orange-backdrop': props.row.touched.includes(props.col.field) }">
              {{ props.value }}
            </q-td>
          </template>
        </q-table>
      </div>

      <BaseDialog
        :show="edit_list.show">
        <BaseActionCard
          square
          class="surface2 q-pa-md"
          :save_label="$t('confirm')"
          @save="confirmEdit"
          @cancel="initListEditData">
          <q-input
            autogrow
            autofocus
            filled
            debounce="300"
            v-model="edit_list.value">
          </q-input>
        </BaseActionCard>
      </BaseDialog>
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
      selected_items: [],
      edit_list: {
        show: false,
        index: null,
        field: null,
        edit_value: null
      },
      touched_items: 0
    }
  },

  computed: {
    list_cols() {
      return [
        {
          name: 'ext_key',
          field: 'ext_key',
          label: this.$t('ext_key'),
          style: 'width: 25%',
          align: 'left'
        },
        {
          name: 'value',
          field: 'value',
          label: this.$t('value'),
          align: 'left',
          style: { "white-space": 'pre-wrap'}
        },
      ]
    },

    shown_list_values() {
      return this.temp_values.map( (row, index) => ({ ...row, index })).filter(
        row => multiMatch(this.list_search, row, ['ext_key', 'value'])
      )
    }
  },

  methods: {
    initTempData() {
      Object.keys(this.temp_data).forEach(k => this.temp_data[k] = this.field[k])
      this.temp_values = this.original_values.map(row => ({ ...row, touched: [] }) )
      this.touched_items = 0
    },

    save() {
      this.saving = true
      this.$axios.all([
        this.$api.put(`field/${this.field._key}`, { ...this.field, ...this.temp_data }),
        this.$api.post(`list/${this.field._key}`, this.temp_values)
      ]).then(() => {
        this.$emit('saved')
        this.saving = false
        this.edit_mode = false
        if (this.field.type == 'choice') this.loadListValues()
      })
    },

    cancel() {
      this.edit_mode = false
      this.initTempData()
    },

    loadListValues() {
      this.$api.get('list', { params: { field_key: this.field._key }})
      .then( resp => {
        this.original_values = [...resp.data]
        this.temp_values = resp.data.map(row => ({ ...row, touched: [] }) )
      })
    },

    addListItem() {
      this.temp_values.unshift({
        field_key: this.field._key,
        ext_key: null,
        value: null,
        touched: ['ext_key', 'value']
      })
    },

    deleteListItems() {
      this.selected_items.forEach(i => this.temp_values.splice(i.index, 1))
    },

    openEditDialog(props) {
      this.edit_list.show = true
      this.edit_list.index = props.row.index
      this.edit_list.field = props.col.field
      this.edit_list.value = this.temp_values[props.row.index][props.col.field]
    },

    confirmEdit() {
      const edit_row = this.temp_values[this.edit_list.index]
      edit_row[this.edit_list.field] = this.edit_list.value
      edit_row.touched.push(this.edit_list.field)
      this.touched_items ++
      this.initListEditData()
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
    this.initTempData()
    if (this.field.type == 'choice') this.loadListValues()
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

<style lang="sass">
.sticky-header-table
  thead tr:first-child th /* bg color is important for th; just specify one */
    background-color: var(--surface-2)
  thead
    position: sticky
    z-index: 1
    top: 0
  tbody tr:last-child td
    border-bottom: .5px solid rgba(255,255,255,.28)
</style>
