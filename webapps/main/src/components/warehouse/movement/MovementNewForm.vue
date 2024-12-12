<template>
  <BaseModalForm
    id="new-position-form"
    :loading="loading"
    max-width="80vw"
    @submit="createMovement"
    @cancel="$router.back()"
  >
    <template #form>
      <q-select
        v-model="movement_type"
        :options="movement_type_options"
        use-input
        filled
        class="q-mb-md col"
        clearable
        input-debounce="100"
        :label="$capitalize($t('warehouse.movement.movement_type'))"
      />

      <!--  SELECT POSITION -->
      <template v-if="movement_type">
        <!-- POSITION FROM -->
        <div class="row items-baseline q-col-gutter-md">
          <BaseAutocompletePositions
            dense
            class="q-mb-md col"
            :load-data="false"
            :label="$capitalize($t('warehouse.movement.position_from_code'))"
            :value="position_from"
            @select="(selection) => (position_from = selection)"
          />
        </div>

        <!-- POSITION TO -->
        <div class="row items-baseline q-col-gutter-md">
          <BaseAutocompletePositions
            dense
            class="q-mb-md col"
            :load-data="false"
            :label="$capitalize($t('warehouse.movement.position_to_code'))"
            :value="position_to"
            @select="(selection) => (position_to = selection)"
          />
        </div>

        <!-- PRODUCT -->
        <div class="row items-baseline q-col-gutter-md">
          <BaseAutocompleteProduct
            dense
            class="q-mb-md col"
            :load-data="false"
            :value="product"
            :label="$capitalize($t('product.label'))"
            @select="(selection) => (product = selection)"
          >
          </BaseAutocompleteProduct>
        </div>

        <!-- SERIAL -->
        <div class="row items-baseline q-col-gutter-md">
          <BaseAutocompleteSerial
            dense
            class="q-mb-md col"
            :load-data="false"
            :value="serial"
            :product_key="product?._key"
            :label="$capitalize($t('serial'))"
            @select="(selection) => (serial = selection)"
          >
          </BaseAutocompleteSerial>
        </div>

        <!-- QUANTITY -->
        <div class="row items-baseline q-col-gutter-md">
          <q-input
            v-model.number="quantity"
            dense
            :label="$capitalize($t('quantity.long'))"
            type="number"
            class="q-mb-md col"
            min="1"
          />
        </div>
      </template>
    </template>
  </BaseModalForm>
</template>

<script setup>
import { ref } from 'vue';
import BaseAutocompletePositions from '@/components/BaseAutocompletePositions.vue';
import BaseAutocompleteProduct from '@/components/BaseAutocompleteProduct.vue';
import BaseAutocompleteSerial from '@/components/BaseAutocompleteSerial.vue';
import BaseModalForm from '@/components/BaseModalForm.vue';

const movement_type_options = ref(['receipt', 'shipment', 'adjustment']);

const movement_type = ref(undefined);

const position_from = ref(undefined);
const position_to = ref(undefined);
const product = ref(undefined);
const serial = ref(undefined);
const quantity = ref(1);

defineProps({
  loading: {
    type: Boolean,
    default: false,
  },
});

function createMovement() {
  console.log('suca');
}
</script>
