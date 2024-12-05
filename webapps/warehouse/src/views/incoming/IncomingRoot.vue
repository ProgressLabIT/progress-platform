<template>
  <q-page class="q-px-md q-pt-lg column fit q-col-gutter-y-lg" id="incoming-root">
    <!-- TITLE -->
    <div class="text-h3 uppercase col-auto text-primary">
      Nuovo Ricevimento
    </div>

    <router-view />



    <!-- <template>
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
      </div>

      <!-      QUANTITY SELECTION
      <template v-if="!selected_quantity || selected_quantity <= 0">
        <QuantitySelectionPage
          :product="selected_product"
          :supplier="selected_supplier"
          @back="selected_product = undefined"
          @quantity-selected="onQuantitySelected"
        ></QuantitySelectionPage>
      </template>

      <!-     POSITION SECTION
      <template v-else-if="!selected_positions">
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

      <!-      CONFIRM INCOMING
      <template v-else>
        <q-scroll-area :visible="false" style="height: 70vh">
          <ConfirmPositionsPage
            :quantity="selected_quantity"
            :positions="selected_positions"
            @position-confirmed="onPositionConfirmed"
            @back="selected_positions = undefined"
          ></ConfirmPositionsPage>
        </q-scroll-area>
        <q-space />
      </template>
    </template> -->

</q-page>

</template>

<script>
// import QuantitySelectionPage from '@/components/incoming/quantity/QuantitySelectionPage.vue';
// import sendEvent from '@/mixins/event.js';
// import ConfirmPositionsPage from 'app/src/components/incoming/position/ConfirmPositionsPage.vue';
// import PositionsPage from 'app/src/components/incoming/position/PositionsPage.vue';
// import { timestamp } from '/src/lib/TimeHandling.js';

// export default {
//   name: 'IncomingRoot',

//   components: {
//     QuantitySelectionPage,
//     PositionsPage,
//     ConfirmPositionsPage,
//   },

//   mixins: [sendEvent],

//   data() {
//     return {
//       selected_supplier: null,
//       selected_product: null,
//       selected_quantity: 0,
//       selected_positions: null,
//       selected_position_keys: null,
//     };
//   },

//   mounted() {
//     this.clear();
//   },

//   methods: {
//     onSupplierSelected(supplier) {
//       this.selected_supplier = supplier;
//     },

//     onProductSelected(product) {
//       this.selected_product = product;
//     },

//     onQuantitySelected(quantity) {
//       if (quantity > 0) {
//         this.selected_quantity = quantity;
//       } else {
//         this.selected_quantity = 0;
//       }
//     },

//     onPositionSelected(incoming_positions) {
//       if (incoming_positions.length <= 0) {
//         return;
//       }
//       let position_left = incoming_positions.length;
//       let quantity_left = this.selected_quantity;
//       let positions = [];
//       for (const position of incoming_positions) {
//         let quantity = Math.floor(quantity_left / position_left);
//         positions.push({
//           ...position,
//           quantity: quantity,
//           locked: false,
//         });
//         position_left -= 1;
//         quantity_left -= quantity;
//       }
//       this.selected_positions = positions;
//     },

//     onPositionConfirmed(exit) {
//       let movements = [];
//       const session_data = this.$store.state.session;
//       for (const position of this.selected_positions) {
//         movements.push({
//           position_from: 'Position/IN',
//           position_to: `Position/${position._key}`,
//           product_key: this.selected_product._key,
//           qt_planned: position.quantity,
//           qt_confirmed: position.quantity,
//           status: 'completed',
//           type: 'receipt',
//           user_key: session_data.user._key,
//           start: timestamp(),
//           end: timestamp(),
//         });
//       }
//       this.sendEvent({
//         event_type: 'ADD_MOVEMENT',
//         event_data: {
//           movements: movements,
//         },
//       });
//       if (!exit) {
//         this.clear();
//       }
//     },

//     clear() {
//       this.selected_supplier = null;
//       this.selected_product = null;
//       this.selected_positions = null;
//       this.selected_quantity = 0;
//     },
//   },
// };
</script>
