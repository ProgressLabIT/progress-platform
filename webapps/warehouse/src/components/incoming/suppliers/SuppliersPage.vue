<template>
  <SuppliersList @supplier-selected="onSupplierSelected"></SuppliersList>
  <q-space />
  <div style="height: 10vh">
    <q-btn-group style="flex-direction: column" spread stretch>
      <q-btn
        color="theme-blue"
        :label="$t('incoming.new')"
        @click="$emit('supplierSelected', 'none')"
      ></q-btn>
    </q-btn-group>
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
