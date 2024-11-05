<template>
  <div id="incoming-root" style="height: 90vh">
    <!--      SUPPLIER SECTION    -->
    <template v-if="!selected_supplier">
      <SuppliersPage @supplier-selected="onSupplierSelected"></SuppliersPage>
    </template>

    <!--      PRODUCT SECTION    -->
    <template v-if="selected_supplier && !selected_product">
      <q-scroll-area :visible="false" style="height: 90vh">
        <ProductsList @product-selected="onProductSelected"></ProductsList>
      </q-scroll-area>
      <q-space />
    </template>

    <!--      QUANTITY SELECTION    -->
    <template v-if="selected_supplier && selected_product">
      <QuantitySelectionPage
        :product="selected_product"
        :supplier="selected_supplier"
        @back="selected_product = undefined"
        @quantity-selected="onQuantitySelected(quantity)"
      ></QuantitySelectionPage>
    </template>
  </div>
</template>

<script>
import ProductsList from '@/components/incoming/products/ProductsList.vue';
import QuantitySelectionPage from '@/components/incoming/quantity/QuantitySelectionPage.vue';
import SuppliersPage from '@/components/incoming/suppliers/SuppliersPage.vue';
export default {
  name: 'IncomingRoot',

  components: { SuppliersPage, ProductsList, QuantitySelectionPage },

  data() {
    return {
      selected_supplier: null,
      selected_product: null,
      selected_quantity: null,
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

    onQantitySelected(quantity) {
      console.log(quantity);
      this.selected_quantity = quantity;
    },
  },
};
</script>
