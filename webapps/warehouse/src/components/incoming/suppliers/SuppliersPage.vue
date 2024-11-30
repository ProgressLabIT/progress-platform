<template>
  <SuppliersList @supplier-selected="onSupplierSelected"></SuppliersList>
  <q-space />
  <div class="q-mx-md">
      <q-btn
        size="md"
        class="full-width"
        color="theme-blue"
        :label="$t('incoming.new')"
        @click="$emit('supplierSelected', 'none')"
      ></q-btn>
  </div>
</template>

<script>
import SuppliersList from '@/components/incoming/suppliers/SuppliersList.vue';
export default {
  name: 'SuppliersPage',

  components: { SuppliersList },

  emits: ['supplierSelected'],

  methods: {
    onSupplierSelected(supplier) {
      this.$emit('supplierSelected', supplier?._key);
    },
  },
};
</script>
