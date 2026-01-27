<template>
  <SlideUpCard
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    @hide="$emit('update:modelValue', false)"
    height="90vh"
  >
    <div class="col column">
      <div class="col-auto q-mb-sm text-h3">
        {{ $t('product') }}
      </div>

      <!-- PRODUCT SEARCH -->
      <SearchOrScan v-model="productFilter" @update:model-value="searchProducts" />

      <!-- PRODUCT LIST -->
      <div class="col-auto q-mt-md q-mb-sm text-h6">
        {{ productListLabel }} ({{ filteredProducts?.length || 0 }})
      </div>

      <CountingProductList
        :products="filteredProducts"
        class="col"
        @select="selectProductForCount"
      />
    </div>
  </SlideUpCard>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { api } from '@/boot/axios';
import { Loading } from 'quasar';
import SearchOrScan from '@/components/SearchOrScan.vue';
import SlideUpCard from '@/components/SlideUpCard.vue';
import CountingProductList from './CountingProductList.vue';

const props = defineProps({
  modelValue: {
    type: Boolean,
    required: true
  },
  positionContents: {
    type: Array,
    default: () => []
  },
  selectedPosition: {
    type: Object,
    default: null
  }
});

const emit = defineEmits(['update:modelValue', 'product-selected']);

const { t: $t } = useI18n();

const productFilter = ref('');
const productListLabel = ref($t('recent'));
const productRows = ref([]);
const productLastResearch = ref(undefined);

// Filter out products that already have inventory in this position
const filteredProducts = computed(() => {
  const existingProducts = props.positionContents.map(p => p.product_key);
  return productRows.value.filter(p => !existingProducts.includes(p._key));
});

async function searchProducts() {
  if (productFilter.value === productLastResearch.value) {
    return;
  }

  Loading.show();
  try {
    const resp = await api.get('product', {
      params: {
        search_string: productFilter.value,
        limit: 100
      }
    });
    productRows.value = resp.data;
    productListLabel.value = $t('results');
    productLastResearch.value = productFilter.value;

    // Auto-select if exactly one product matches the search (after filtering)
    if (filteredProducts.value.length === 1 && filteredProducts.value[0].code === productFilter.value) {
      selectProductForCount(filteredProducts.value[0]);
      productFilter.value = '';
    }
  } catch (error) {
    console.error('Error searching products:', error);
    productRows.value = [];
  } finally {
    Loading.hide();
  }
}

function selectProductForCount(product) {
  emit('product-selected', product);
  emit('update:modelValue', false);
  productFilter.value = '';
}
</script>

<style lang="sass" scoped>
</style>
