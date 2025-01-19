<template>
  <q-scroll-area :visible="false" :style="form_height">
    <!--- LOADING -->

    <template v-if="loading_label">
      <q-inner-loading
        :showing="true"
        :label="loading_label"
        label-class="text-teal"
        label-style="font-size: 1.1em"
      />
    </template>

    <!-- SELECT TEMPLATE -->
    <template v-else-if="stage === 'select_template'">
      <q-list bordered separator>
        <q-item
          v-for="template in print_templates"
          :key="template._key"
          v-ripple
          clickable
          @click="selectTemplate(template)"
        >
          <q-item-label>{{ template.name }}</q-item-label>
        </q-item>
      </q-list>
    </template>

    <!-- SELECT COPIES -->
    <template v-else-if="stage === 'select_copies'">
      <div>
        <QuantitySelector
          :heading="$t('select_copies')"
          :initial_qty="0"
          :show_buttons="false"
          selector_style="height: 80px"
          @quantity-changed="
            (qt) => {
              selected_copies = qt;
            }
          "
        ></QuantitySelector>
      </div>
      <div>
        <div class="fit row justify-center items-start content-center">
          <q-btn
            color="theme-blue"
            :label="$t('back')"
            class="col-6"
            @click="stage = 'select_template'"
          ></q-btn>
          <q-btn
            color="theme-blue"
            :label="$t('next')"
            class="col-6"
            @click="selectPrinter(null)"
          ></q-btn>
        </div>
      </div>
    </template>

    <!-- SELECT PRINTER -->
    <template v-else-if="stage === 'select_printer'">
      <q-list bordered separator>
        <q-item
          v-for="printer in printers"
          :key="printer._key"
          v-ripple
          clickable
          :disable="!printer.ready"
          @click="selectPrinter(printer)"
        >
          <q-item-label>{{ printer.name }}</q-item-label>
          <q-item-label caption>{{ printer.description }}</q-item-label>
        </q-item>
      </q-list>
    </template>

    <!-- PRINT_DONE -->
    <template v-else-if="stage === 'print_done'">
      <div class="text-subtitle1 q-py-xl text-center">Print done!</div>
    </template>

    <div class="fit row justify-center items-start content-center">
      <q-btn
        v-if="stage !== 'printing'"
        color="theme-blue"
        :label="stage === 'print_done' ? $t('close') : $t('cancel')"
        class="col-12"
        @click="closeForm()"
      ></q-btn>
    </div>
  </q-scroll-area>
</template>

<script>
import { exportFile } from 'quasar';
import { generate } from '@pdfme/generator';
import BrowserPrint, { Printer } from 'browserprint-es';
import QuantitySelector from '@/components/QuantitySelector.vue';

export default {
  name: 'PrintLabelForm',

  components: { QuantitySelector },

  props: {
    // product: {
    //   type: Object,
    //   default: undefined,
    // },
    // supplier: {
    //   type: Object,
    //   default: undefined,
    // },
    // containers: {
    //   type: Object,
    //   default: undefined,
    // },
    print_templates: {
      type: Object,
      required: true,
    },
    available_height: {
      type: Number,
      required: true,
    },
  },

  data() {
    return {
      printers: [],
      stage: 'select_template',
      selected_template: undefined,
      loading_label: undefined,
      selected_copies: 0,
      selected_printers: undefined,
    };
  },

  computed: {
    form_height() {
      return 'height: ' + (this.available_height - 30) + 'px';
    },
  },

  mounted() {
    this.stage = 'select_template';
    this.selected_template = undefined;
    this.selected_copies = 0;
    this.selected_printers = undefined;
    this.loading_label = undefined;
    this.loadPrinters();
  },

  beforeUnmount() {
    this.stage = 'select_template';
    this.selected_template = undefined;
    this.selected_copies = 0;
    this.selected_printers = undefined;
    this.loading_label = undefined;
    this.printers = [];
  },

  methods: {
    closeForm() {
      this.$bus.emit('close-footer');
    },

    selectTemplate(template) {
      this.loading_label = this.$t('print_label.loading_template');
      this.$api.get(`print-template/${template._key}`).then(
        (response) => {
          this.loading_label = undefined;
          this.selected_template = response.data;
          this.stage = 'select_copies';
        },
        () => {
          this.$q.notify({
            type: 'negative',
            position: 'top',
            message: this.$t('alerts.template_error'),
          });
          this.loading_label = undefined;
        }
      );
    },

    selectCopies() {
      this.stage = 'select_printer';
    },

    prepareInputs() {
      // Needed to parse input type to load images as base64
      const inputs = [];
      for (const schema of this.selected_template.template.schemas) {
        let schemaFields = [];
        for (const [fieldName /*, fieldProps*/] of Object.entries(schema)) {
          //if (fieldProps.type === 'image') {
          //  try {
          //    const base64 = formModel[fieldName] // Image URL
          //      ? await loadImage(formModel[fieldName])
          //      : ''; // empty string will not render any image. Background, if present, will be visibile.
          //    schemaFields.push([fieldName, base64]);
          //  } catch (err) {
          //    window.alert(
          //      'Error while generating the image. Please contact the system administrator.'
          //    );
          //    console.log(err);
          //  }
          //} else {
          schemaFields.push([fieldName, /*formModel[fieldName]*/ '']);
          //}
        }
        inputs.push(Object.fromEntries(schemaFields));
      }
      return inputs;
    },

    selectPrinter(printer) {
      this.selected_printers = printer;
      this.loading_label = 'printing';
      let template = this.selected_template.template;

      generate({ template, inputs: this.prepareInputs() }).then(
        (data) => {
          exportFile('test-no-mime.pdf', new Blob([data], { type: 'application/pdf' }))
          //() => {
          // printer.device.sendFile(new Blob([data]));
          //printer.device.sendAsync("^XA^FO200,200^A0N36,36^FDTest Label^FS^XZ");
          this.loading_label = undefined;
          setTimeout(() => {
            this.loading_label = undefined;
            this.stage = 'print_done';
          }, 3000);
          /*printer.device.sendFile(data).then(
            () => {
              setTimeout(() => {
                this.loading_label = undefined;
                this.stage = 'print_done';
              }, 3000);
            },
            () => {
              this.loading_label = undefined;
              this.$q.notify({
                type: 'negative',
                position: 'top',
                message: this.$t('alerts.print_error'),
              });
            }
          );*/
        },
        () => {
          this.loading_label = undefined;
          this.$q.notify({
            type: 'negative',
            position: 'top',
            message: this.$t('alerts.template_error'),
          });
        }
      );
    },

    loadPrinters() {
      this.printers = [];
      this.loading_label = this.$t('loading_printers');
      BrowserPrint.getLocalDevicesAsync().then((devices) => {
        if (!devices?.printer) {
          this.loading_label = undefined;
          return;
        }
        for (const device of devices.printer) {
          let printer = new Printer(device);
          printer.getStatusAsync().then(
            (status) => {
              this.printers.push({
                name: device.name,
                description: device.uid,
                device: device,
                status: status,
                ready: true,
              });
            },
            () => {
              this.printers.push({
                name: device.name,
                description: device.uid,
                device: device,
                status: 'offline',
                ready: false,
              });
            }
          );
        }
        this.loading_label = undefined;
      });
    },
  },
};
</script>
