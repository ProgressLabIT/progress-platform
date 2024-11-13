<template>
  <q-scroll-area :visible="false" :style="form_height">
    <!-- SELECT QUANTITY -->
    <template v-if="!containers">
      <div class="text-subtitle1 q-py-xl text-center">
        {{ $t('incoming.positions.create_container_form.title') }}
      </div>
      <div>
        <QuantitySelector
          :initial_qty="0"
          :show_buttons="false"
          selector_style="height: 80px"
          @quantity-changed="
            (qt) => {
              selected_quantity = qt;
            }
          "
        ></QuantitySelector>
      </div>
      <div>
        <div class="fit row justify-center items-start content-center">
          <q-btn
            color="theme-blue"
            :label="$t('next')"
            class="col-6"
            @click="createContainers()"
          ></q-btn>
          <q-btn
            color="theme-blue"
            :label="$t('cancel')"
            class="col-6"
            @click="closeForm()"
          ></q-btn>
        </div>
      </div>
    </template>

    <!-- CONTAINERS CREATED -->
    <template v-else>
      <div class="q-pa-md">
        <q-table
          flat
          bordered
          grid
          :title="$t('incoming.positions.create_container_form.containers')"
          :rows="containers"
          :columns="columns"
          row-key="_key"
          :rows-per-page-options="[0]"
          hide-header
          hide-bottom
        >
        </q-table>
      </div>
      <div>
        <div class="fit row justify-center items-start content-center">
          <q-btn
            color="theme-blue"
            :label="$t('incoming.positions.create_container_form.print_label')"
            class="col-6"
            @click="showPrintLabelBottomSheet()"
          ></q-btn>
          <q-btn
            color="theme-blue"
            :label="$t('next')"
            class="col-6"
            @click="createContainers()"
          ></q-btn>
          <q-btn
            color="theme-blue"
            :label="$t('cancel')"
            class="col-6"
            @click="closeForm()"
          ></q-btn>
        </div>
      </div>
    </template>
  </q-scroll-area>
</template>

<script>
import QuantitySelector from '@/components/QuantitySelector.vue';

const columns = [
  {
    name: 'code',
    required: true,
    align: 'left',
    field: (row) => row.code,
    format: (val) => `${val}`,
    sortable: true,
  },
  {
    name: 'description',
    required: true,
    align: 'left',
    field: (row) => row.description,
    format: (val) => `${val}`,
    sortable: true,
  },
];

export default {
  name: 'CreateContainerForm',

  components: { QuantitySelector },

  props: {
    available_height: {
      type: Number,
      required: true,
    },
  },

  setup() {
    return {
      columns,
    };
  },

  data() {
    return {
      stage: 'select_quantity',
      selected_quantity: 0,
      containers: undefined,
    };
  },

  computed: {
    form_height() {
      return 'height: ' + (this.available_height - 30) + 'px';
    },
  },

  mounted() {
    this.stage = 'select_quantity';
    this.selected_quantity = 0;
    this.containers = undefined;
  },

  beforeUnmount() {
    this.stage = 'select_quantity';
    this.selected_quantity = 0;
    this.containers = undefined;
  },

  methods: {
    closeForm() {
      this.$bus.emit('close-footer');
    },

    createContainers() {
      this.containers = [];
      for (let step = 0; step < this.selected_quantity; step++) {
        this.containers.push({
          _key: step,
          code: `cont ${step}`,
          description: `container ${step}`,
        });
      }
    },

    showPrintLabelBottomSheet() {
      let print_templates = [{}];
      this.$bus.emit('show-print-templates', {
        print_templates: print_templates,
        containers: this.containers,
      });
    },
  },
};
</script>
