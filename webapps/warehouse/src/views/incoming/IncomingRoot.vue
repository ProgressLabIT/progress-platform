<template>
  <div id="incoming-root">
    <SuppliersList
      v-if="!selected_supplier"
      @supplier-selected="onSupplierSelected"
    ></SuppliersList>
    <ProductsList
      v-if="selected_supplier && !selected_product"
      @product-selected="onProductSelected"
    ></ProductsList>
    <IncomingProduct
      v-if="selected_supplier && selected_product"
      :product="selected_product"
      :supplier="selected_supplier"
    ></IncomingProduct>
  </div>
</template>

<script>
import ProductsList from '@/components/incoming/ProductsList.vue';
import SuppliersList from '@/components/incoming/SuppliersList.vue';
import IncomingProduct from 'app/src/components/incoming/IncomingProduct.vue';
export default {
  name: 'IncomingRoot',

  components: { SuppliersList, ProductsList, IncomingProduct },

  data() {
    return {
      selected_supplier: null,
      selected_product: null,
    };
  },

  mounted() {
    this.selected_product = null;
    this.selected_product = null;
  },

  methods: {
    onSupplierSelected(supplier) {
      console.log(supplier);
      this.selected_supplier = supplier;
    },

    onProductSelected(product) {
      console.log(product);
      this.selected_product = product;
    },
  },
};
</script>
