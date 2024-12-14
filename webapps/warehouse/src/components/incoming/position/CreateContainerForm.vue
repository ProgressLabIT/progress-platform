<template>
  <div class="column col">

    <!-- SELECT QUANTITY -->
    <template v-if="!containers.length">
      <div class="text-h2 col-auto">
        {{ $t('position_new_prompt') }}
      </div>
      <QuantitySelector
        v-model="selected_quantity"
        :initial_qty="0"
        :show_buttons="false"
        class="col"
        :max="props.max"
      />
      <div class="col-auto">
        <q-btn
          color="theme-blue"
          class="full-width"
          :label="$t('next')"
          @click="createContainers()"
        />
      </div>
      <div class="q-my-md">
        <q-btn
          color="theme-blue"
          class="full-width"
          :label="$t('cancel')"
          @click="$emit('hide')"
        />
      </div>
    </template>

    <!-- CERATING CONTAINERS -->

    <template v-else-if="creating_containers">
      <q-inner-loading
        :showing="creating_containers"
        :label="$t('position_creating')"
        label-class="text-teal"
        label-style="font-size: 1.1em"
      />
    </template>

    <!-- CONTAINERS CREATED -->
    <div class="column col q-gutter-y-md" v-else>
      <div class="text-h1">
        {{ $t('position_created', selected_quantity) }}
      </div>
      <div class="row q-col-gutter-xs q-py-lg">
        <div
          v-for="position in containers"
          :key="position._key"
          class="col-auto"
        >
          <q-chip
            outline
            class="text-body1"
          >
            {{ position.code }}
          </q-chip>
        </div>
      </div>
      <q-space />
      <q-btn
        color="theme-blue"
        :label="$t('print_label')"
        @click="printPositionLabels()"
      />
      <q-btn
        color="theme-blue"
        :label="$t('next')"
        @click="$emit('select', containers);"
      />
      <q-btn
        color="theme-blue"
        :label="$t('cancel')"
        @click="$emit('hide')"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onBeforeUnmount } from 'vue';
import { api as $api } from '@/boot/axios';
import QuantitySelector from '@/components/QuantitySelector.vue';
import { useQuasar } from 'quasar';
import { useI18n } from 'vue-i18n';
import { printPositionLabel } from '@/lib/print';

const $q = useQuasar();
const $t = useI18n().t;
const $emit = defineEmits(['hide']);

const selected_quantity = ref(0);
const containers = ref([]);
const creating_containers = ref(false);
// const print_templates = ref([]);

const props = defineProps({
  max: {
    type: Number,
    default: 100,
  },
});


function resetForm() {
  selected_quantity.value = 0;
  containers.value = undefined;
}

onBeforeUnmount(() => resetForm());

async function createContainers() {
  creating_containers.value = true;
  console.log('createContainers');
  Array(selected_quantity.value).keys().forEach(() => {
    $api.post('position', {
      owned: true,
      available: true,
      disposable: false,
    })
    .then((resp) => containers.value.push(resp.data.detail))
    .catch((err) => {
      $q.notify({
        type: 'negative',
        position: 'top',
        message: $t(
          'alerts.cannot_create_position'
        ) + err,
      });
    })
  })
  creating_containers.value = false
}

function printPositionLabels() {
  containers.value.forEach((position) => {
    printPositionLabel(position.code);
  });
}
// function showPrintLabelBottomSheet() {
//   $api
//     .get('print-template', {
//       params: { context: 'position', context_key: 'IN' },
//     })
//     .then((data) => {
//       if (data && data?.data?.length > 0) {
//         print_templates.value= data?.data;

//       } else {
//         $q.notify({
//           type: 'negative',
//           position: 'top',
//           message: $t(
//             'alerts.cannot_find_print_template'
//           ),
//         });
//       }
//     });
// }

</script>
