<template>
  <q-card
    square
    class="surface1 product-card"
    :class="{ faded: !product.active }"
    @dblclick="$router.push(to_product_route)"
  >
    <img
      v-if="product.image & showImage"
      style="object-fit: cover"
      :src="`/media/product/${product._key}/image.jpg`"
      class="fit"
      :style="product.active ? '' : 'filter:grayscale(1)'"
    />
    <div
      class="absolute-top q-pa-sm"
      :style="`background-color: ${
        showImage
          ? $q.dark.isActive
            ? 'rgba(0,0,0,.7)'
            : 'rgba(230,230,230,.8)'
          : 'transparent'
      }`"
      @mouseenter="overDesc = true"
      @mouseleave="overDesc = false"
    >
      <div class="text-h3 display">
        {{ product.code }}
      </div>
      <div
        class="text-uppercase low-text px-0 pb-1"
        :class="{ nowrap: !overDesc }"
      >
        {{ product.description }}
      </div>
      <div
        v-show="showImage && product.image ? overDesc : true"
        class="px-0 pb-1"
        :class="{ nowrap: !overDesc }"
      >
        <q-chip
          v-for="tag in product.tags"
          :key="tag._key"
          :label="tag.name"
          :color="tag.color ?? 'theme-grey'"
          dense
        />
      </div>
    </div>
    <ProductCardActions
      class="absolute-bottom"
      :product="product"
      @show-delete="showDelete = true"
    >
    </ProductCardActions>

    <!-- DELETE CONFIRMATION -->
    <div
      v-if="showDelete"
      class="absolute-full surface1 column"
      :class="showImage ? 'q-pa-md' : 'q-pa-sm'"
    >
      <div>
        {{ $t('product.confirm_delete_question') }}
      </div>
      <div class="display weight-medium q-mt-sm">
        {{ product.code }}
      </div>
      <q-space />
      <div class="row justify-between">
        <q-btn color="theme-red" size="12px" @click.stop="trash">
          {{ $t('confirm') }}
        </q-btn>
        <q-btn color="theme-grey" size="12px" @click.stop="showDelete = false">
          {{ $t('cancel') }}
        </q-btn>
      </div>
    </div>
  </q-card>
</template>

<script>
import { mapActions } from 'vuex';
import ProductCardActions from '@/components/ProductCardActions.vue';

export default {
  name: 'ProductCard',

  components: {
    ProductCardActions,
  },

  props: {
    product: {
      type: Object,
      required: true,
    },
    showImage: {
      type: Boolean,
      default: false,
    },
  },

  data() {
    return {
      overCard: false,
      overDesc: false,
      showDelete: false,
    };
  },

  computed: {
    to_product_route() {
      return {
        name: 'productHome',
        params: {
          product_key: this.product._key,
        },
        query: {
          back_to: 'productList',
          ...this.$route.query,
        },
      };
    },
  },

  methods: {
    ...mapActions(['moveToTrash', 'restoreProduct']),

    trash() {
      this.moveToTrash(this.product);
      this.$q.notify({
        progress: true,
        message: this.$t('product.snackbars.delete_confirmed', {
          code: this.product.code,
        }).toUpperCase(),
        color: 'theme-background',
        multiline: true,
        actions: [
          {
            label: this.$t('confirm'),
            color: 'theme-blue',
          },
          {
            label: this.$t('undo'),
            color: 'theme-orange',
            handler: () => this.restoreProduct(this.product._key),
          },
        ],
      });
    },
  },
};
</script>

<style lang="sass" scoped>
.product-card
  height: 100%
  border: thin solid rgba(255, 255, 255, .12)
  & .q-img__content > div
    padding: 8px !important

.faded
  filter: brightness(.7)
</style>
