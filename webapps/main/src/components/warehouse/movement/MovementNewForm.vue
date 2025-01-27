<template>
  <BaseModalForm
    id="new-position-form"
    :loading="loadingVal"
    max-width="80vw"
    :enable-save="saveButtonEnabled"
    @submit="
      () => {
        createMovement();
        $router.back();
      }
    "
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
        <!-- POSITION -->
        <div class="row items-baseline q-col-gutter-md">
          <BaseAutocompletePositions
            dense
            class="q-mb-md col"
            :load-data="false"
            :label="$capitalize($t('warehouse.movement.position_code'))"
            :value="position"
            :disable="loadingVal"
            :options="availablePositions"
            @select="
              (selection) => {
                position = selection;
                getAvailableProducts();
                getAvailableSerials();
              }
            "
          />
        </div>

        <!-- PRODUCT -->
        <div v-if="position" class="row items-baseline q-col-gutter-md">
          <BaseAutocompleteProduct
            v-if="movement_type === 'receipt'"
            dense
            class="q-mb-md col"
            :load-data="false"
            :value="product"
            :disable="loadingVal || serial"
            :label="$capitalize($t('product.label'))"
            @select="(selection) => productSelection(selection)"
          >
          </BaseAutocompleteProduct>
          <q-select
            v-else
            :model-value="product"
            dense
            filled
            class="q-mb-md col"
            option-label="code"
            :options="availableProducts"
            :disable="loadingVal || serial"
            :label="$capitalize($t('product.label'))"
            @update:model-value="(selection) => productSelection(selection)">
            <template #option="scope">
              <q-item v-bind="scope.itemProps" :id="scope.opt.code">
                <q-item-section>
                  <q-item-label class="highlight">
                    {{ scope.opt.code }}
                  </q-item-label>
                  <q-item-label caption lines="2">
                    {{ scope.opt.description }}
                  </q-item-label>
                </q-item-section>
              </q-item>
            </template>
          </q-select>
        </div>

        <!-- SERIAL -->
        <div v-if="position && requiresSerialCode" class="row items-baseline q-col-gutter-md">
          <q-input
            v-if="movement_type === 'receipt'"
            v-model="newSerialCode"
            dense
            class="q-mb-md col"
            :label="$t('serial')"
            filled
          />

          <BaseAutocompleteSerial
            v-else
            dense
            class="q-mb-md col"
            :options="availableSerials"
            :load-data="false"
            :value="serial"
            :disable="loadingVal"
            :label="$capitalize($t('serial'))"
            @select="(selection) => serialSelection(selection)"
          >
          </BaseAutocompleteSerial>
        </div>

        <!-- QUANTITY -->
        <div v-if="product" class="row items-baseline q-col-gutter-md">
          <q-input
            v-if="!requiresSerialCode"
            v-model.number="quantity"
            filled
            dense
            :disable="loadingVal"
            :label="$capitalize($t('quantity.long'))"
            type="number"
            class="q-mb-md col"
            :min="qtyMin"
            :max="qtyMax"
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
import { api } from 'app/src/boot/axios';

const movement_type_options = ref(['receipt', 'shipment', 'adjustment']);

const movement_type = ref(undefined);

const position = ref(undefined);
const product = ref(undefined);
const serial = ref(undefined);
const requiresSerialCode = ref(undefined);
const newSerialCode = ref(undefined)
const quantity = ref(1);

const store = useStore();

const qtyMin = ref(1);
const qtyMax = ref(undefined);

const saveButtonEnabled = ref(false);

const originalPosition = ref(undefined);
const availableProducts = ref([]);
const availableSerials = ref([]);
const availablePositions = ref([]);

watch(movement_type, getAvailablePositions);

watch(quantity, () => {
  saveButtonEnabled.value = !validateMovementError();
});

watch(newSerialCode, () => {
  saveButtonEnabled.value = !validateMovementError();
});

const props = defineProps({
  loading: {
    type: Boolean,
    default: false,
  },
});
const loadingVal = ref(props.loading);

function clean() {
  position.value = undefined;
  product.value = undefined;
  serial.value = undefined;
  quantity.value = 1;
  qtyMax.value = undefined;
  originalPosition.value = undefined;
  availableProducts.value = [];
  availablePositions.value = [];
}

async function productSelection(selection) {
  quantity.value = 1;
  qtyMax.value = undefined;
  originalPosition.value = undefined;
  product.value = selection;
  serial.value = undefined;
  availableSerials.value = undefined;
  if (product.value && movement_type.value === 'receipt') {
    const { data } = await api.get(`product/${selection._key}`)
    requiresSerialCode.value = !!data?.traceability_level
  } else {
    getAvailableSerials();
  }
  getOriginalPosition();
}

function serialSelection(selection) {
  quantity.value = 1;
  qtyMax.value = undefined;
  originalPosition.value = undefined;
  serial.value = selection;
  if (serial.value) {
    api.get(`/product/${serial.value.product_key}`).then(
      (data) => {
        product.value = data.data;
        getOriginalPosition();
      },
      () => {
        product.value = undefined;
      },
    );
  } else {
    getOriginalPosition();
  }
}

function getOriginalPosition() {
  if (
    !product?.value ||
    movement_type?.value === 'receipt' ||
    !position?.value?._key
  ) {
    return;
  }
  loadingVal.value = true;
  let params = {
    position_key: position.value._key,
    product_key: product.value._key,
    strict: true,
  };
  if (serial.value) {
    params.serial_keys = serial.value._key;
  }
  api
    .get('/inventory', {
      params,
    })
    .then(
      (data) => {
        originalPosition.value = data.data[0];
        quantity.value = originalPosition.value?.quantity;
        if (movement_type.value === 'shipment') {
          qtyMax.value = quantity.value;
        }
        loadingVal.value = false;
      },
      () => {
        originalPosition.value = undefined;
        loadingVal.value = false;
      },
    );
}

function getAvailablePositions() {
  clean();
  if (!movement_type?.value) {
    return;
  }

  if (movement_type.value === 'receipt') {
    loadingVal.value = true;
    api.get('/position').then(
      (data) => {
        availablePositions.value = data.data;
        loadingVal.value = false;
      },
      () => {
        availablePositions.value = [];
        loadingVal.value = false;
      },
    );
  } else {
    api.get('/inventory/positions').then(
      (data) => {
        availablePositions.value = data.data;
        loadingVal.value = false;
      },
      () => {
        availablePositions.value = [];
        loadingVal.value = false;
      },
    );
  }
}

function getAvailableProducts() {
  availableProducts.value = [];
  product.value = undefined;
  quantity.value = 1;
  qtyMax.value = undefined;
  originalPosition.value = undefined;
  if (!position?.value) {
    return;
  }
  if (movement_type?.value === 'receipt') {
    loadingVal.value = true;
    api.get('/product').then(
      (data) => {
        availableProducts.value = data.data;
        loadingVal.value = false;
      },
      () => {
        availableProducts.value = [];
        loadingVal.value = false;
      },
    );
  } else {
    if (position?.value?._key) {
      loadingVal.value = true;
      api
        .get('/inventory/products', {
          params: { position_key: position?.value?._key },
        })
        .then(
          (data) => {
            availableProducts.value = data.data;
            loadingVal.value = false;
          },
          () => {
            availableProducts.value = [];
            loadingVal.value = false;
          },
        );
    } else {
      availableProducts.value = [];
    }
  }
}

function getAvailableSerials() {
  availableSerials.value = [];
  serial.value = undefined;
  if (!position?.value) {
    return;
  }
  if (movement_type?.value !== 'receipt' && position?.value?._key) {
    loadingVal.value = true;
    let params = { position_key: position?.value?._key };
    if (product.value) {
      params.product_key = product.value._key;
    }
    api
      .get('/inventory/serials', {
        params: params,
      })
      .then(
        (data) => {
          availableSerials.value = data.data;
          loadingVal.value = false;
        },
        () => {
          availableSerials.value = [];
          loadingVal.value = false;
        },
      );
  }
}

function createMovement() {
  const session_data = store.state.session;

  let error = validateMovementError();

  if (error) {
    Notify.create({
      message: error,
      type: 'negative',
      color: 'theme-orange',
    });
    return;
  }

  let position_from_id = 'Position/OUT';
  let position_to_id = 'Position/OUT';
  let position_id = undefined;
  if (position?.value?._key) {
    position_id = `Position/${position?.value?._key}`;
  }

  switch (movement_type.value) {
    case 'receipt':
      position_to_id = position_id;
      break;
    case 'shipment':
      position_from_id = position_id;
      break;
    case 'adjustment':
      position_from_id = position_id;
      position_to_id = position_id;
      break;
    default:
      return 'Invalid movement type';
  }

  const now = timestamp()

  let movement = {
    position_from: position_from_id,
    position_to: position_to_id,
    product_key: product?.value?._key,
    serial_key: serial?.value?._key,
    serial_code: newSerialCode.value,
    qt_planned: quantity.value, // 1 by default if not set otherwise
    qt_confirmed: quantity.value, // 1 by default if not set otherwise
    status: 'completed',
    type: movement_type.value,
    user_key: session_data.user._key,
    start: now,
    end: now,
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

function validateMovementError() {
  if (!position?.value?._key || !product.value?._key || !quantity?.value) {
    return 'missing fields';
  }
  switch (movement_type.value) {
    case 'receipt':
      if (requiresSerialCode.value === true && newSerialCode.value?.length === 0) {
        return 'Indicate a serial code';
      }
      if (requiresSerialCode.value === false && quantity.value <= 0) {
        return 'quantity should be > 0';
      }
      break;
    case 'shipment':
      if (!originalPosition?.value) {
        return 'cannot find position to update';
      }
      if (quantity.value > originalPosition.value.quantity) {
        return `quantity should be <= ${originalPosition.value.quantity}`;
      }
      break;
    case 'adjustment':
      if (!originalPosition?.value) {
        return 'cannot find position to update';
      }
      break;
    default:
      return 'Invalid movement type';
  }
  return undefined;
}
</script>
