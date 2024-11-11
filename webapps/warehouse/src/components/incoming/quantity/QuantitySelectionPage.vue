<template>
  <div v-if="loading">
    {{ $t('incoming.quantity.loading') }}
  </div>
  <div v-else class="q-pa-md">
    <div class="text-subtitle1 text-center">
      {{ $t('incoming.quantity.title') }}
    </div>
    <div style="height: 40vh">
      <div ref="qtyarea" class="q-pa-md row justify-center">
        <div>
          {{ product.name }}
        </div>
        <div>
          {{ supplier.name }}
        </div>
        <q-card
          v-touch-repeat.mouse="handleRepeat"
          class="custom-area cursor-pointer bg-primary text-white shadow-2 relative-position row flex-center"
        >
          <div class="text-center">{{ quantity }}</div>
        </q-card>
      </div>
    </div>
    <div style="height: 30vh">
      <div class="fit row justify-center items-start content-center">
        <q-btn
          color="theme-blue"
          :label="$t('incoming.quantity.div10')"
          class="col-3"
          @click="divideQty"
        ></q-btn>
        <q-btn
          color="theme-blue"
          :label="$t('incoming.quantity.min10')"
          class="col-3"
          @click="quantity = quantity > 10 ? quantity - 10 : 0"
        ></q-btn>
        <q-btn
          color="theme-blue"
          :label="$t('incoming.quantity.plus10')"
          class="col-3"
          @click="quantity = quantity + 10"
        ></q-btn>
        <q-btn
          color="theme-blue"
          :label="$t('incoming.quantity.mul10')"
          class="col-3"
          @click="quantity = quantity * 10"
        ></q-btn>
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
          @click="showPrintLabelBottomSheet(true)"
        ></q-btn>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'QuantitySelectionPage',

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
    handleRepeat(info) {
      let qtyRect = this.$refs.qtyarea.getBoundingClientRect();
      if (info.position.left > qtyRect.x + qtyRect.width / 2) {
        this.quantity++;
      } else if (this.quantity > 0) {
        this.quantity--;
      }
    },

    divideQty() {
      if (this.quantity <= 0) {
        this.quantity = 0;
      } else {
        this.quantity = Math.floor(this.quantity / 10);
      }
    },
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

<style lang="sass" scoped>
.custom-area
  width: 96%
  height: 250px
  border-radius: 3px
  padding: 8px
</style>
