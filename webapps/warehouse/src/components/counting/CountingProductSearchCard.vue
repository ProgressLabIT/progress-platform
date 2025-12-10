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
        {{ productListLabel }} ({{ productRows?.length || 0 }})
      </div>

      <q-scroll-area class="col">
        <q-list>
          <q-item
            v-for="product in productRows"
            :key="product._key"
            clickable
            dense
            class="content-card q-my-xs q-py-sm"
            :class="getProductColor(product)"
            @click="selectProductForCount(product)"
          >
            <q-item-section side>
              <q-icon :name="product.traceability_level ? 'mdi-cube-scan' : 'mdi-apps'" />
            </q-item-section>
            <q-item-section>
              <q-item-label class="highlight">{{ product.code }}</q-item-label>
              <q-item-label caption class="">{{ product.description }}</q-item-label>
            </q-item-section>
          </q-item>
        </q-list>
      </q-scroll-area>
    </div>
  </SlideUpCard>
</template>

<script setup>
import { ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { api } from '@/boot/axios';
import { Loading } from 'quasar';
import SearchOrScan from '@/components/SearchOrScan.vue';
import SlideUpCard from '@/components/SlideUpCard.vue';

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
const productListLabel = ref('Recenti');
const productRows = ref([]);
const productLastResearch = ref(undefined);

function getProductColor(product) {
  return product.traceability_level ? 'bg-green-backdrop' : 'bg-blue-backdrop';
}

async function searchProducts() {
  if (productFilter.value === productLastResearch.value) {
    return;
  }

  Loading.show();
  const resp = await api.get('product', {
    params: {
      search_string: productFilter.value,
      limit: 100
    }
  });
  const existingProducts = props.positionContents.map(p => p.product_key);
  const subset = resp.data.filter(p => !existingProducts.includes(p._key));
  if (subset.length === 1 && subset[0].code === productFilter.value) {
    selectProductForCount(subset[0]);
    productFilter.value = '';
  } else {
    productRows.value = subset;
    productListLabel.value = 'Risultati';
    productLastResearch.value = productFilter.value;
  }
  Loading.hide();
}

function selectProductForCount(product) {
  emit('product-selected', product);
  emit('update:modelValue', false);
  productFilter.value = '';
}
</script>

<style lang="sass" scoped>
.content-card
  border-radius: 5px
  border: 1px solid transparent
</style>




