<template>
  <q-scroll-area :visible="false" :style="form_height">
    <!-- SELECT TEMPLATE -->
    <template v-if="stage === 'select_template'">
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
      <div class="text-subtitle1 q-py-xl text-center">
        {{ $t('printLabel.selectCopiesTitle') }}
      </div>
      <div>
        <QuantitySelector
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
            @click="selectCopies()"
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
          @click="selectPrinter(printer)"
        >
          <q-item-label>{{ printer.name }}</q-item-label>
          <q-item-label caption>{{ printer.description }}</q-item-label>
        </q-item>
      </q-list>
    </template>

    <!-- PRINTING -->
    <template v-else-if="stage === 'printing'">
      <q-inner-loading
        :showing="stage === 'printing'"
        label="Printing..."
        label-class="text-teal"
        label-style="font-size: 1.1em"
      />
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
const printers = [
  { _key: '111', name: 'PR1', description: 'PR1 desc' },
  { _key: '222', name: 'PR2', description: 'PR2 desc' },
  { _key: '333', name: 'PR3', description: 'PR3 desc' },
];

import QuantitySelector from '@/components/QuantitySelector.vue';

export default {
  name: 'PrintLabelForm',

  components: { QuantitySelector },

  props: {
    product: {
      type: Object,
      default: undefined,
    },
    supplier: {
      type: Object,
      default: undefined,
    },
    containers: {
      type: Object,
      default: undefined,
    },
    print_templates: {
      type: Object,
      required: true,
    },
    available_height: {
      type: Number,
      required: true,
    },
  },

  setup() {
    return {
      printers,
    };
  },

  data() {
    return {
      stage: 'select_template',
      selected_template: undefined,
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
  },

  beforeUnmount() {
    this.stage = 'select_template';
    this.selected_template = undefined;
    this.selected_copies = 0;
    this.selected_printers = undefined;
  },

  methods: {
    closeForm() {
      this.$bus.emit('close-footer');
    },

    selectTemplate(template) {
      this.selected_template = template;
      this.stage = 'select_copies';
    },

    selectCopies() {
      this.stage = 'select_printer';
    },

    selectPrinter(printer) {
      this.selected_printers = printer;
      this.stage = 'printing';

      setTimeout(() => {
        this.stage = 'print_done';
      }, 3000);
    },
  },
};
</script>
