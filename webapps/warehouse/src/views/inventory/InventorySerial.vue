<template>
  <div class="col column q-col-gutter-y-sm">
    <div class="row col-auto q-col-gutter-sm">
      <div class="col-6">
        <SearchOrScan
          v-model="serialCodeFilter"
          label="Seriale"
          @update:model-value="search"
        />
      </div>
      <div class="col-6">
        <q-input
          filled
          dense
          clearable
          input-class="text-uppercase"
          label="Prodotto"
          :debounce="300"
          v-model="productCodeFilter"
          @update:model-value="search"
        >
          <template #append>
            <q-icon name="mdi-filter" />
          </template>
        </q-input>
      </div>
    </div>

    <div class="col-auto row items-center q-gutter-x-sm q-mb-sm text-h6">
      <div>{{ $t('results') }}</div>
      <q-chip size="xs" color="theme-grey">
        <div class="smaller highlight">{{ serialList.length }}</div>
      </q-chip>
    </div>

    <q-scroll-area class="col">

      <div class="col scroll q-my-md column">
        <q-card
          v-for="item in serialList"
          :key="item._key"
          v-ripple
          bordered
          flat
          class="surface2 q-px-md q-py-md q-mb-sm"
          @click="onItemClick(item)"
        >
          <div class="text-h6 text-low">{{ item.product_code }}</div>
          <div class="text-body1 highlight">{{ item.serial_code }}</div>
          <div class="text-caption">{{ item.path.map(p => p.position_code).join(' → ') || 'IN' }}</div>
        </q-card>
      </div>
    </q-scroll-area>

  </div>
</template>

<script setup>
import { Notify } from 'quasar';
import { ref, computed } from 'vue';
import SearchOrScan from '@/components/SearchOrScan.vue';
import { api } from 'app/src/boot/axios';
import { useI18n } from 'vue-i18n';

const { t: $t } = useI18n();
const serialCodeFilter = ref('');
const productCodeFilter = ref('');
const results = ref([]);

const serialList = computed(() => {
  return results.value.filter(s => s.product_code.includes(productCodeFilter.value));
});


function search() {
  api.get('inventory', { params: {
    serial_search: serialCodeFilter.value,
    product_search: productCodeFilter.value
  }})
  .then(response => {
    results.value = response.data;
  })
  .catch(error => {
    Notify.create({
      message: error.response.data.message,
      position: 'top',
      color: 'red',
      icon: 'error',
    });
  });
}

</script>

<style lang="scss" scoped>
</style>
