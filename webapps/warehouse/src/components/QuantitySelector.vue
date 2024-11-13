<template>
  <div ref="qtyarea" class="q-pa-md row justify-center">
    <q-card
      v-touch-repeat.mouse="handleRepeat"
      class="custom-area cursor-pointer bg-primary text-white shadow-2 relative-position row flex-center"
      :style="selector_style"
    >
      <div class="text-center">{{ quantity }}</div>
    </q-card>
    <q-space />
  </div>
  <div class="fit row justify-center items-start content-center">
    <template v-if="show_buttons">
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
      <q-space />
    </template>
  </div>
</template>

<script>
export default {
  name: 'QuantitySelector',

  props: {
    initial_qty: {
      type: Number,
      default: 0,
    },
    show_buttons: {
      type: Boolean,
      default: false,
    },
    selector_style: {
      type: String,
      default: '',
    },
  },

  emits: ['quantityChanged'],

  data() {
    return {
      quantity: 0,
    };
  },

  watch: {
    quantity: {
      handler() {
        this.$emit('quantityChanged', this.quantity);
      },
    },
  },

  mounted() {
    this.quantity = this.initial_qty;
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
