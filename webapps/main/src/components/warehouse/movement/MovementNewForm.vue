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
            v-if="movement_type !== 'receipt'"
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
            v-if="movement_type === 'receipt'"
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
import { Notify } from 'quasar';
import { ref, watch } from 'vue';
import { useStore } from 'vuex';
import BaseAutocompletePositions from '@/components/BaseAutocompletePositions.vue';
import BaseAutocompleteProduct from '@/components/BaseAutocompleteProduct.vue';
import BaseAutocompleteSerial from '@/components/BaseAutocompleteSerial.vue';
import BaseModalForm from '@/components/BaseModalForm.vue';
import { sendEvent } from '@/composables/event.js';
import { timestamp } from '@/lib/TimeHandling';

const movement_type_options = ref(['receipt', 'shipment', 'adjustment']);

const movement_type = ref(undefined);

const position_from = ref(undefined);
const position_to = ref(undefined);
const product = ref(undefined);
const serial = ref(undefined);
const quantity = ref(1);

const store = useStore();

watch(movement_type, () => {
  clean();
});

defineProps({
  loading: {
    type: Boolean,
    default: false,
  },
});

function clean() {
  position_from.value = undefined;
  position_to.value = undefined;
  product.value = undefined;
  serial.value = undefined;
  quantity.value = undefined;
}

function createMovement() {
  const session_data = store.state.session;

  let position_from_id = 'Position/IN';
  if (position_from?.value?._key) {
    position_from_id = `Position/${position_from?.value?._key}`;
  }

  let position_to_id = 'Position/XXX';
  if (position_to?.value?._key) {
    position_to_id = `Position/${position_to?.value?._key}`;
  }

  if (!validateMovement()) {
    return;
  }

  let movement = {
    position_from: position_from_id,
    position_to: position_to_id,
    product_key: product?.value?._key,
    qt_planned: quantity.value,
    qt_confirmed: quantity.value,
    status: 'completed',
    type: movement_type.value,
    user_key: session_data.user._key,
    start: timestamp(),
    end: timestamp(),
  };

  sendEvent({
    event_type: 'ADD_MOVEMENT',
    event_data: {
      movement: movement,
    },
  })
    .then(() => {
      Notify.create({
        message: 'Movimenti registrati',
        type: 'positive',
        timeout: 1500,
      });
    })
    .catch((err) => {
      Notify.create({
        message: err,
        type: 'negative',
        color: 'theme-orange',
      });
    });
}

function validateMovement() {
  switch (movement_type.value) {
    case 'receipt':
      if (
        !position_from?.value?._key ||
        !product.value?._key ||
        !quantity?.value
      ) {
        Notify.create({
          message: 'missing fields',
          type: 'negative',
          color: 'theme-orange',
        });
        return false;
      }
      break;
    case 'shipment':
      break;
    case 'adjustment':
      break;
    default:
      Notify.create({
        message: 'Invalid movement type',
        type: 'negative',
        color: 'theme-orange',
      });
      return false;
  }
  return true;
}
</script>
