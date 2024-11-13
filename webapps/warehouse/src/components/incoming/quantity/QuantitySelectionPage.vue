<template>
  <div v-if="loading">
    {{ $t('incoming.quantity.loading') }}
  </div>
  <div v-else class="q-pa-md">
    <div class="text-subtitle1 text-center">
      {{ $t('incoming.quantity.title') }}
    </div>
    <div style="height: 5vh">
      <div>
        <div>
          {{ product.name }}
        </div>
        <div>
          {{ supplier.name }}
        </div>
      </div>
    </div>
    <div style="height: 35vh">
      <QuantitySelector
        :initial_qty="0"
        :show_buttons="true"
        @quantity-changed="
          (qt) => {
            quantity = qt;
          }
        "
      ></QuantitySelector>
    </div>
    <div style="height: 40vh">
      <div class="fit row justify-center items-start content-center">
        <q-btn
          color="theme-blue"
          :label="$t('back')"
          class="col-6"
          @click="$emit('back')"
        ></q-btn>
        <q-btn
          color="theme-blue"
          :label="$t('next')"
          class="col-6"
          @click="$emit('quantitySelected', quantity)"
        ></q-btn>
        <q-btn
          v-if="print_templates"
          color="theme-blue"
          :label="$t('incoming.quantity.print_label')"
          class="col-12"
          @click="
            (event) => {
              event.stopPropagation();
              showPrintLabelBottomSheet();
            }
          "
        ></q-btn>
      </div>
    </div>
  </div>
</template>

<script>
import QuantitySelector from '@/components/QuantitySelector.vue';
export default {
  name: 'QuantitySelectionPage',

  components: { QuantitySelector },

  props: {
    product: {
      type: Object,
      required: true,
    },
    supplier: {
      type: Object,
      required: true,
    },
  },

  emits: ['back', 'quantitySelected'],

  data() {
    return {
      quantity: 0,
      show_print_label: false,
      print_templates: undefined,
      selected_templates: undefined,
      loading: true,
    };
  },

  mounted() {
    this.loading = true;

    if (this.product) {
      this.$api
        .get('print-template', {
          params: { context: 'product', context_key: this.product._key },
        })
        .then((data) => {
          if (data && data?.data.length > 0) {
            this.print_templates = data?.data;
          } else {
            this.print_templates = undefined;
          }
          this.loading = false;
        });
    }
  },

  methods: {
    showPrintLabelBottomSheet() {
      this.$bus.emit('show-print-templates', {
        print_templates: this.print_templates,
        product: this.product,
        supplier: this.supplier,
      });
      /*let actions = [];
      for (const template of this.print_templates) {
        actions.push({
          label: template.name,
          id: template._key,
        });
      }
      this.$q
        .bottomSheet({
          title: 'title',
          message: 'Bottom Sheet message',
          actions: actions,
        })
        .onOk((action) => {
          console.log('Action chosen:', action.id);
        })
        .onCancel(() => {
          // console.log('Dismissed')
        })
        .onDismiss(() => {
          // console.log('I am triggered on both OK and Cancel')
        });*/
    },
  },
};
</script>
