<template>
  <div class="q-pa-lg column full-height">
    <q-form class="full-height column" @submit="save">
      <div class="row justify-between items-start">
        <div class="col-10 row q-col-gutter-md">
          <!-- Field type -->
          <div class="col-4">
            <q-select
              v-model="temp_data.type"
              :options="field_types"
              emit-value
              map-options
              :disable="!editMode"
              filled
              :label="$t('type')"
            >
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
              v-model="temp_data.name"
              :rules="[(value) => !!value || $t('field_required_alert')]"
              filled
              :disable="!editMode"
              :label="$t('name')"
              stack-label
            />
          </div>

          <!-- Field default Label -->
          <div class="col-4">
            <q-input
              v-model="temp_data.default_label"
              filled
              :label="$t('label')"
              :disable="!editMode"
              stack-label
            />
          </div>

          <!-- Field default hint -->
          <div class="col-12">
            <q-input
              v-model="temp_data.default_hint"
              filled
              :disable="!editMode"
              :label="$t('hint')"
              stack-label
              autogrow
            />
          </div>
        </div>

        <!-- ACTION BUTTONS -->
        <div class="col-auto">
          <template v-if="!editMode">
            <BaseTooltipIcon
              icon="mdi-pencil"
              :tooltip="$capitalize($t('edit'))"
              :color="$theme.blue"
              @icon-click="editMode = true"
            />

            <BaseTooltipIcon
              icon="mdi-delete"
              :tooltip="$capitalize($t('delete'))"
              :color="$theme.red"
              @icon-click="show_delete = true"
            />
          </template>

          <template v-else>
            <div class="col column q-gutter-md">
              <q-btn
                type="submit"
                size="12px"
                color="theme-blue"
                :loading="saving"
                :label="$t('save')"
              />

              <q-btn
                size="12px"
                color="theme-grey"
                :label="$t('cancel')"
                @click="cancel"
              />
            </div>
          </template>
        </div>
      </div>

      <!-- List values if necessary -->
      <template v-if="is_choice">
        <div
          class="row full-width items-baseline q-col-gutter-md q-my-md q-px-xs"
        >
          <div class="text-h3 col-auto q-px-none">
            {{ $t('value', 2) }}
          </div>

          <div
            v-if="shown_list_values.length === search_limit"
            class="smaller col-auto text-low"
          >
            {{ $t('first_x_shown', { x: search_limit }) }}
          </div>

          <q-space />

          <template v-if="editMode">
            <div class="col-auto">
              <q-btn
                size="10px"
                icon="mdi-plus"
                color="theme-blue"
                :label="$t('add')"
                @click="addListItem"
              />
            </div>

            <div v-if="selected_items.length" class="col-auto">
              <q-btn
                size="10px"
                icon="mdi-delete"
                color="theme-red"
                :label="$t('delete')"
                @click="deleteListItems"
              >
              </q-btn>
            </div>
          </template>

          <div>
            <q-input
              v-model="list_search"
              :disable="search_disabled"
              debounce="500"
              filled
              dense
              :label="$capitalize($t('search'))"
            >
              <template #append>
                <q-icon name="mdi-magnify" />
              </template>
            </q-input>

            <q-tooltip
              v-if="search_disabled"
              delay="200"
              anchor="top middle"
              self="center middle"
            >
              {{ $t('save_or_cancel_before_change') }}
            </q-tooltip>
          </div>
        </div>

        <div class="col">
          <q-table
            id="list-values"
            v-model:selected="selected_items"
            :columns="list_cols"
            :rows="shown_list_values"
            color="primary"
            class="full-height"
            table-class="text-high "
            card-class="surface2 shadow-2"
            flat
            dense
            :loading="table_loading"
            :separator="editMode ? 'none' : 'horizontal'"
            square
            virtual-scroll
            hide-bottom
            :selection="editMode ? 'multiple' : 'none'"
            :rows-per-page-options="[0]"
            row-key="index"
          >
            <template #loading>
              <q-inner-loading showing color="primary" />
            </template>

            <template #body-cell="props">
              <q-td :props="props" class="q-pl-none">
                <div :class="getItemClasses(props)">
                  <q-input
                    v-if="editMode"
                    v-model="temp_values[props.row.index][props.col.field]"
                    :disable="!editMode"
                    filled
                    dense
                    autogrow
                    input-style="white-space: pre-wrap"
                  />
                  <div v-else>
                    {{ props.value }}
                  </div>
                </div>
              </q-td>
            </template>
          </q-table>
        </div>
      </template>
    </q-form>

    <BaseDialog :show="show_delete">
      <BaseActionCard
        :title="$t('field_delete')"
        :save-label="$t('confirm')"
        save-color="theme-red"
        @save="deleteField"
        @cancel="show_delete = false"
      >
        {{ $t('field_delete_text') }}
      </BaseActionCard>
    </BaseDialog>
  </div>
</template>

<script>
import BaseActionCard from '@/components/BaseActionCard.vue';
import BaseDialog from '@/components/BaseDialog.vue';
import BaseTooltipIcon from '@/components/BaseTooltipIcon.vue';
import form from '@/mixins/form.js';

export default {
  name: 'CounterDetail',

  components: {
    BaseActionCard,
    BaseDialog,
    BaseTooltipIcon,
  },

  mixins: [form],

  props: {
    field: {
      type: Object,
      required: true,
    },
  },

  emits: ['reload'],

  data() {
    return {
      temp_data: {
        type: null,
        name: null,
        default_label: null,
        default_hint: null,
      },
      table_loading: false,
      saving: false,
      original_values: [],
      temp_values: [],
      show_delete: false,
      editMode: false,
      list_search: null,
      selected_items: [],
      search_limit: 100,
    };
  },

  computed: {
    list_cols() {
      return [
        {
          name: 'value',
          field: 'value',
          label: this.$t('value'),
          align: 'left',
          style: { 'white-space': 'pre-wrap' },
        },
        {
          name: 'ext_key',
          field: 'ext_key',
          label: this.$t('ext_key'),
          style: 'width: 25%',
          align: 'left',
        },
      ];
    },

    is_choice() {
      return this.field.type == 'choice';
    },

    shown_list_values() {
      // Map must happen before the filter so the index is preserved, otherwise the same index would refer to different records depending on the filter
      return this.temp_values.map((row, index) => ({ ...row, index }));
    },

    new_or_updated_items() {
      // This is the list of values to send to the POST endpoint
      return this.temp_values.filter((row) => {
        if (row.new) {
          return true;
        } else if (row.delete) {
          return false;
        } else {
          const original = this.original_values.find((v) => v._key == row._key);
          return row.value != original.value || row.ext_key != original.ext_key;
        }
      });
    },

    deleted_items() {
      // This is the list of values to send to the DELETE endpoint
      return this.temp_values.filter((row) => row.delete);
    },

    search_disabled() {
      return (
        this.editMode &&
        (!!this.new_or_updated_items.length || !!this.deleted_items.length)
      );
    },
  },

  watch: {
    field: {
      handler() {
        this.initTempFieldData();
        if (this.is_choice) {
          this.loadListValues();
        }
        this.editMode = false;
      },
    },
    list_search: 'loadListValues',
  },

  mounted() {
    this.initTempFieldData();
    if (this.is_choice) {
      this.loadListValues();
    }
  },

  methods: {
    initTempFieldData() {
      Object.keys(this.temp_data).forEach(
        (k) => (this.temp_data[k] = this.field[k]),
      );
    },

    initTempValues() {
      this.temp_values = this.original_values.map((row) => ({
        ...row,
        new: false,
        delete: false,
      }));
    },

    getItemClasses({ row, col, value }) {
      return row.delete
        ? 'bg-red-backdrop text-strike'
        : row.new
          ? 'bg-green-backdrop text-italic'
          : value !==
              this.original_values.find(({ _key }) => _key === row._key)[
                col.field
              ]
            ? 'bg-orange-backdrop'
            : '';
    },

    save() {
      this.saving = true;
      const calls = [
        this.$api.put(`field/${this.field._key}`, {
          ...this.field,
          ...this.temp_data,
        }),
        this.$api.post(`list/${this.field._key}`, this.new_or_updated_items),
      ];

      if (this.deleted_items.length) {
        // Need to use URLSearchParams to avoid square brackets in the query param name (e.g. ?value_key[]=XXX -> ?value_key=XXX)
        const params = new URLSearchParams();
        this.deleted_items.forEach((item) =>
          params.append('value_key', item._key),
        );
        calls.push(this.$api.delete(`list/${this.field._key}`, { params }));
      }

      Promise.all(calls).then(() => {
        this.$emit('reload');
        this.saving = false;
        this.editMode = false;
        if (this.is_choice) {
          this.loadListValues();
        }
      });
    },

    cancel() {
      this.selected_items = [];
      this.initTempFieldData();
      this.initTempValues();
      this.editMode = false;
    },

    loadListValues() {
      this.table_loading = true;
      this.$api
        .get('list', {
          params: {
            field_key: this.field._key,
            search: this.list_search,
            limit: this.search_limit,
          },
        })
        .then((resp) => {
          this.original_values = resp.data;
          this.initTempValues();
          this.table_loading = false;
        });
    },

    addListItem() {
      this.temp_values.unshift({
        field_key: this.field._key,
        ext_key: null,
        value: this.$t('new'),
        new: true,
        delete: false,
      });
    },

    deleteListItems() {
      // Flag for deletion original values, remove temporary ones
      this.selected_items.forEach(
        (i) => (this.temp_values[i.index].delete = true),
      );
      this.temp_values = this.temp_values.filter((v) => !(v.delete && v.new));
      this.selected_items = [];
    },

    initListEditData() {
      this.edit_list = {
        show: false,
        index: null,
        field: null,
      };
    },

    deleteField() {
      this.$api.delete(`field/${this.field._key}`).then(() => {
        this.$q.notify({
          message: this.$t('field_delete_success'),
          color: 'theme-green',
          timeout: 1500,
          position: 'top',
        });
        this.$emit('reload');
        this.$router.push({ name: 'counterLibrary' });
      });
    },
  },
};
</script>

<style lang="sass">
#list-values thead
  position: sticky
  z-index: 1
  top: 0

  tr:first-child th /* bg color is important for th; just specify one */
    background-color: var(--surface-2)
    padding-top: 8px
    padding-bottom: 8px
    border-bottom: 1px solid rgba(255, 255, 255, .3)

.table-no-hover
  td::before
    // remove hover highlight
    background-color: transparent
</style>
