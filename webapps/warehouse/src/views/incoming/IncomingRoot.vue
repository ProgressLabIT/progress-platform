<template>
  <!-- TITLE -->
  <div class="text-subtitle1 q-py-xl text-left" style="height: 100px">
    {{ $t('incoming.new') }}
  </div>
  <div id="incoming-root" style="height: 90vh">
    <!--      SUPPLIER SECTION    -->
    <template v-if="!selected_supplier">
      <SuppliersPage @supplier-selected="onSupplierSelected"></SuppliersPage>
    </template>

    <!--      PRODUCT SECTION    -->
    <template v-else-if="!selected_product">
      <q-scroll-area :visible="false" style="height: 90vh">
        <ProductsList @product-selected="onProductSelected"></ProductsList>
      </q-scroll-area>
      <q-space />
    </template>

    <template v-else>
      <!-- HEADER -->
      <div
        class="row justify-center items-start content-left"
        style="height: 100px"
      >
        <div class="col-10">{{ $t('incoming.product_caption') }}</div>
        <div v-if="selected_quantity" class="col-2">
          {{ $t('incoming.quantity_caption') }}
        </div>
        <div class="col-10">{{ selected_product.code }}</div>
        <div v-if="selected_quantity" class="col-2">
          {{ selected_quantity }}
        </div>

        <div v-if="selected_position" class="col-12">
          {{ $t('incoming.position_caption') }}
        </div>
        <div v-if="selected_position" class="col-12">
          {{ selected_position.code }}
        </div>
      </div>

      <!--      QUANTITY SELECTION    -->
      <template v-if="!selected_quantity || selected_quantity <= 0">
        <div style="height: 70vh">
          <QuantitySelectionPage
            :product="selected_product"
            :supplier="selected_supplier"
            @back="selected_product = undefined"
            @quantity-selected="onQuantitySelected"
          ></QuantitySelectionPage>
        </div>
        <q-space />
      </template>

      <!--      POSITION SECTION    -->
      <template v-else-if="!selected_position">
        <q-scroll-area :visible="false" style="height: 70vh">
          <PositionsPage
            :product="selected_product"
            :supplier="selected_supplier"
            :quantity="selected_quantity"
            @position-selected="onPositionSelected"
            @back="selected_quantity = undefined"
          ></PositionsPage>
        </q-scroll-area>
        <q-space />
      </template>

      <!--      CONFIRM INCOMING    -->
      <template v-else>
        <q-scroll-area :visible="false" style="height: 10vh"> </q-scroll-area>
        <div class="fit row justify-center items-start content-center">
          <q-btn
            color="theme-blue"
            :label="$t('incoming.confirm_and_close')"
            class="col-12"
            @click="confirm(true)"
          ></q-btn>
          <q-btn
            color="theme-blue"
            :label="$t('incoming.confirm_and_start_again')"
            class="col-12"
            @click="confirm(false)"
          ></q-btn>
          <q-btn
            color="theme-blue"
            :label="$t('cancel')"
            class="col-12"
            @click="selected_position = undefined"
          ></q-btn>
        </div>
        <q-space />
      </template>
    </template>
  </div>
</template>

<script>
import ProductsList from '@/components/incoming/products/ProductsList.vue';
import QuantitySelectionPage from '@/components/incoming/quantity/QuantitySelectionPage.vue';
import SuppliersPage from '@/components/incoming/suppliers/SuppliersPage.vue';
import PositionsPage from 'app/src/components/incoming/position/PositionsPage.vue';

export default {
  name: 'IncomingRoot',

  components: {
    SuppliersPage,
    ProductsList,
    QuantitySelectionPage,
    PositionsPage,
  },

  data() {
    return {
      selected_supplier: null,
      selected_product: null,
      selected_quantity: 0,
      selected_position: null,
    };
  },

  mounted() {
    this.clear();
  },

  methods: {
    onSupplierSelected(supplier) {
      this.selected_supplier = supplier;
    },

    onProductSelected(product) {
      this.selected_product = product;
    },

    onQuantitySelected(quantity) {
      if (quantity > 0) {
        this.selected_quantity = quantity;
      } else {
        this.selected_quantity = 0;
      }
    },

    onPositionSelected(position) {
      this.selected_position = position;
    },

    confirm(exit) {
      //TODO: do something
      if (!exit) {
        this.clear();
      }
    },

    clear() {
      this.selected_product = null;
      this.selected_product = null;
      this.selected_position = null;
      this.selected_quantity = 0;
    },
  },
};
</script>
