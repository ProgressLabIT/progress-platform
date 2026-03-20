<template>
  <LoadingSignal v-if="!data_ready" />

  <div v-else class="row full-height">
    <div class="full-height column col">
      <div class="row justify-between q-pr-md"></div>

      <div
        class="row q-mt-md q-px-lg q-py-sm text-h6 text-uppercase weight-bold"
      >
        <div class="col-3">
          {{ $t('name') }}
        </div>
        <div class="col-2">
          {{ $t('host') }}
        </div>
        <div class="col-1">
          {{ $t('port') }}
        </div>
        <div class="col-2">
          {{ $t('printer.type') }}
        </div>
        <div class="col-2">
          {{ $t('printer.timeout') }}
        </div>
      </div>

      <q-separator />

      <!-- PRINTER LIST -->
      <div class="scroll col">
        <div
          v-for="(printer, index) in printer_list"
          :key="index"
          :dense="dense"
          :readonly="!editMode"
          class="row pointer q-px-lg q-py-xs medium full-width"
          :class="{
            'alternate-row': index % 2 === 0,
            'bg-blue-backdrop': printer === selected_printer_obj,
          }"
          style="white-space: nowrap"
          @click="selectPrinter(printer)"
        >
          <div class="col-3">
            {{ $capitalize(printer.name) }}
          </div>
          <div class="col-2">
            {{ $capitalize(printer.host) }}
          </div>
          <div class="col-1">
            {{ $capitalize(printer.port) }}
          </div>
          <div class="col-2">
            {{ (printer.type || '').toUpperCase() }}
          </div>
          <div class="col-2">
            {{ printer.timeout_seconds ? printer.timeout_seconds + 's' : '' }}
          </div>
        </div>
      </div>

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
          @click="show_new_printer_form = true"
        >
        </q-btn>
        <q-btn
          v-if="selected_printer_obj && editMode"
          color="theme-red"
          class="col-auto"
          size="12px"
          :label="$t('remove_printer')"
          :readonly="!editMode"
          @click="show_delete = true"
        >
        </q-btn>
      </div>
    </div>

    <BaseDialog
      :show="show_new_printer_form"
      :no-backdrop-dismiss="false"
      @close="show_new_printer_form = false"
    >
      <PrinterNew
        @close="show_new_printer_form = false"
        @add-printer="addPrinter"
      >
      </PrinterNew>
    </BaseDialog>

    <BaseDialog
      :show="show_delete"
      :no-backdrop-dismiss="false"
      @close="show_delete = false"
    >
      <BaseActionCard
        :title="$t('printer_delete')"
        :save-label="$t('confirm')"
        save-color="theme-red"
        @save="deletePrinter"
        @cancel="show_delete = false"
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
      selected_printer_obj: undefined,
    };
  },

  computed: {
    selected_printer() {
      return this.printer_list.findIndex(
        (printer) => printer === this.selected_printer_obj,
      );
    },
  },
  methods: {
    selectPrinter(printer) {
      this.selected_printer_obj = printer;
    },
    addPrinter(printer) {
      this.show_new_printer_form = false;
      let temp_values = this.printer_list;
      temp_values.push(printer);
      this.$emit('update:printer_list', temp_values);
      this.$emit('reload');
    },

    deletePrinter() {
      this.show_delete = false;
      let temp_values = this.printer_list;
      temp_values.splice(this.selected_printer, 1);
      this.$emit('update:printer_list', temp_values);
      this.$emit('reload');
    },
  },
};
</script>
