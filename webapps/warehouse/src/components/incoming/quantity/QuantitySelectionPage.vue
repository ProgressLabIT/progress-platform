<template>
  <div class="q-pa-md">
    <div class="text-subtitle1 q-py-xl text-center">
      {{ $t('incoming.quantity.title') }}
    </div>
    <div style="height: 50vh">
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
          :label="$t('incoming.quantity.back')"
          class="col-6"
          @click="$emit('back')"
        ></q-btn>
        <q-btn
          color="theme-blue"
          :label="$t('incoming.quantity.next')"
          class="col-6"
          @click="$emit('quantitySelected', quantity)"
        ></q-btn>
        <q-btn
          color="theme-blue"
          :label="$t('incoming.quantity.print_label')"
          class="col-12"
        ></q-btn>
      </div>
    </div>
  </div>

  <ModalBottomContainer
    :show="show_print_label"
    @close="show_print_label = false"
  >
    <template #content>
      <CameraCodeScanner @scan="onScan" @load="onLoad"></CameraCodeScanner>
    </template>
  </ModalBottomContainer>
</template>

<script>
import ModalBottomContainer from '@/components/ModalBottomContainer.vue';

export default {
  name: 'QuantitySelectionPage',

  components: {
    ModalBottomContainer,
  },

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

  setup() {
    return {};
  },

  data() {
    return {
      quantity: 0,
      show_print_label: false,
    };
  },

  methods: {
    handleRepeat(info) {
      console.log(info.position);
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
  },
};
</script>

<style lang="sass" scoped>
.grid-style-transition
  transition: transform .28s, background-color .28s

.custom-area
  width: 96%
  height: 250px
  border-radius: 3px
  padding: 8px
</style>
