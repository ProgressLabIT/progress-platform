<template>
  <div class="q-pa-md">
    <div class="text-subtitle1 q-py-xl text-center">
      {{ $t('incoming.products.title') }}
    </div>

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
        <div class="text-center">{{ count }}</div>
      </q-card>
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
  name: 'IncomingProduct',

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

  setup() {
    return {};
  },

  data() {
    return {
      count: 0,
      show_print_label: false,
    };
  },

  methods: {
    handleRepeat(info) {
      console.log(info.position);
      let qtyRect = this.$refs.qtyarea.getBoundingClientRect();
      if (info.position.left > qtyRect.x + qtyRect.width / 2) {
        this.count++;
      } else if (this.count > 0) {
        this.count--;
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
