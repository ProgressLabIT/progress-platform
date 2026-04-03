<template>
  <LoadingSignal v-if="!data_ready" />

  <div v-else class="row full-height">
    <div class="full-height column col">
      <div class="row justify-between q-pr-md"></div>

      <q-table
        class="col q-mt-md transparent"
        flat
        :rows="tableRows"
        :columns="columns"
        row-key="_rowId"
        :pagination="{ rowsPerPage: 0 }"
        hide-bottom
        :dense="dense"
      >
        <template #body="props">
          <q-tr
            :props="props"
            :class="{
              'alternate-row': props.row._rowId % 2 === 0,
            }"
            style="white-space: nowrap"
          >
            <q-td key="name" :props="props">
              {{ $capitalize(props.row.name) }}
            </q-td>
            <q-td key="host" :props="props">
              {{ $capitalize(props.row.host) }}
            </q-td>
            <q-td key="port" :props="props">
              {{ $capitalize(props.row.port) }}
            </q-td>
            <q-td key="type" :props="props">
              {{ (props.row.type || '').toUpperCase() }}
            </q-td>
            <q-td key="dpi" :props="props">
              {{ props.row.type === 'zpl' ? (props.row.dpi || 203) : '' }}
            </q-td>
            <q-td key="offset" :props="props">
              {{
                props.row.type === 'zpl'
                  ? `${props.row.offset_x || 0}, ${props.row.offset_y || 0}`
                  : ''
              }}
            </q-td>
            <q-td key="timeout" :props="props">
              {{ props.row.timeout_seconds ? props.row.timeout_seconds + 's' : '' }}
            </q-td>
            <q-td key="actions" :props="props" class="text-right">
              <q-btn
                v-if="editMode"
                flat
                icon="mdi-pencil"
                size="xs"
                :label="$t('edit')"
                @click.stop="editPrinter(props.row._rowId)"
              />
              <q-btn
                v-if="editMode"
                flat
                class="q-ml-sm"
                icon="mdi-delete"
                size="xs"
                color="theme-red"
                :label="$t('delete')"
                @click.stop="confirmDeletePrinter(props.row._rowId)"
              />
            </q-td>
          </q-tr>
        </template>
      </q-table>

      <q-separator />

      <!-- PRINTER LIST COUNT -->
      <div class="row flex-center smaller q-py-xs">
        {{ printer_list.length }} {{ $t('of') }} {{ printer_list.length }}
      </div>

      <div class="row q-pa-md justify-between">
        <q-btn
          v-if="editMode"
          color="theme-blue"
          class="col-auto"
          size="12px"
          :label="$t('add_printer')"
          @click="openNewPrinterForm"
        >
        </q-btn>
      </div>
    </div>

    <BaseDialog
      :show="show_new_printer_form"
      :no-backdrop-dismiss="false"
      @close="closePrinterForm"
    >
      <PrinterNew
        :printer="editing_printer_index !== null ? printer_list[editing_printer_index] : null"
        @close="closePrinterForm"
        @add-printer="addPrinter"
        @update-printer="updatePrinter"
      >
      </PrinterNew>
    </BaseDialog>

    <BaseDialog
      :show="show_delete"
      :no-backdrop-dismiss="false"
      @close="closeDeleteDialog"
    >
      <BaseActionCard
        :title="$t('printer_delete')"
        :save-label="$t('confirm')"
        save-color="theme-red"
        @save="deletePrinter"
        @cancel="closeDeleteDialog"
      >
        {{ $t('printer_delete_text') }}
      </BaseActionCard>
    </BaseDialog>
  </div>
</template>

<script>
import BaseActionCard from '@/components/BaseActionCard.vue';
import BaseDialog from '@/components/BaseDialog.vue';
import LoadingSignal from '@/components/LoadingSignal.vue';
import PrinterNew from '@/components/settings/printers/PrinterNew.vue';
import form from '@/mixins/form.js';

export default {
  name: 'PrintersTable',

  components: {
    BaseDialog,
    PrinterNew,
    BaseActionCard,
    LoadingSignal,
  },

  mixins: [form],

  props: {
    editMode: {
      type: Boolean,
      required: true,
    },
    dense: {
      type: Boolean,
      default: false,
    },
    printer_list: {
      type: Array,
      default: () => [],
    },
  },

  emits: ['reload', 'update:printer_list'],

  data() {
    return {
      data_ready: true,
      search_text: undefined,
      show_new_printer_form: false,
      show_delete: false,
      deleting_printer_index: null,
      editing_printer_index: null,
    };
  },

  computed: {
    tableRows() {
      return this.printer_list.map((printer, index) => ({
        ...printer,
        _rowId: index,
      }));
    },
    columns() {
      return [
        { name: 'name', label: this.$t('name'), field: 'name', align: 'left', sortable: true },
        { name: 'host', label: this.$t('host'), field: 'host', align: 'left', sortable: true },
        { name: 'port', label: this.$t('port'), field: 'port', align: 'left', sortable: true },
        { name: 'type', label: this.$t('printer.type'), field: 'type', align: 'left', sortable: true },
        { name: 'dpi', label: this.$t('printer.dpi'), field: 'dpi', align: 'left' },
        { name: 'offset', label: this.$t('printer.offset'), field: 'offset', align: 'left' },
        { name: 'timeout', label: this.$t('printer.timeout'), field: 'timeout_seconds', align: 'left' },
        { name: 'actions', label: '', field: 'actions', align: 'right' },
      ];
    },
  },
  methods: {
    openNewPrinterForm() {
      this.editing_printer_index = null;
      this.show_new_printer_form = true;
    },
    closePrinterForm() {
      this.show_new_printer_form = false;
      this.editing_printer_index = null;
    },
    confirmDeletePrinter(index) {
      this.deleting_printer_index = index;
      this.show_delete = true;
    },
    closeDeleteDialog() {
      this.show_delete = false;
      this.deleting_printer_index = null;
    },
    addPrinter(printer) {
      this.closePrinterForm();
      const temp_values = [...this.printer_list, printer];
      this.$emit('update:printer_list', temp_values);
      this.$emit('reload');
    },

    editPrinter(index) {
      this.editing_printer_index = index;
      this.show_new_printer_form = true;
    },

    updatePrinter(updatedPrinter) {
      if (this.editing_printer_index === null) {
        this.closePrinterForm();
        return;
      }
      const temp_values = [...this.printer_list];
      temp_values.splice(this.editing_printer_index, 1, updatedPrinter);
      this.$emit('update:printer_list', temp_values);
      this.closePrinterForm();
      this.$emit('reload');
    },

    deletePrinter() {
      this.show_delete = false;
      if (this.deleting_printer_index === null || this.deleting_printer_index < 0) return;
      const temp_values = [...this.printer_list];
      temp_values.splice(this.deleting_printer_index, 1);
      this.$emit('update:printer_list', temp_values);
      this.deleting_printer_index = null;
      this.$emit('reload');
    },
  },
};
</script>
