<template>
  <SlideUpCard
    :model-value="selectedItem !== undefined"
    height="95vh"
    @hide="() => selectedItem = undefined"
  >

    <!-- ITEM SELECTION (QUANTITY / SERIALS)-->
    <template v-if="step==='selection'">
      <ItemSerialsSelection v-if="selectedItem.type === 'serial'" />
      <ItemQuantitySelection v-else :max="selectedItem.qt_planned"/>
      <div class="row q-gutter-x-md">

      </div>
      <q-btn
        color="theme-blue"
        :label="$t('print_label')"
        unelevated
        class="full-width q-mb-md"
        @click="printProductLabel(selectedItem.product_code, selectedItem.product_description)"
      />
    </template>

    <!-- DESTINATION -->
    <template v-else-if="step==='destination'">
      TEST

    </template>

    <template v-else>

    </template>


  </SlideUpCard>
</template>

<script setup>
import { storeToRefs } from 'pinia';
import { ref } from 'vue';
import { useI18n } from 'vue-i18n';
import SlideUpCard from 'app/src/components/SlideUpCard.vue';
import ItemQuantitySelection from 'app/src/components/lists/ItemQuantitySelection.vue';
import ItemSerialsSelection from 'app/src/components/lists/ItemSerialsSelection.vue';
import { printProductLabel } from 'app/src/lib/print';
import { useListsStore } from 'stores/lists';
import { onBeforeRouteLeave, useRouter } from 'vue-router';


const lists = useListsStore();
const { t: $t } = useI18n();
const { selectedItem } = storeToRefs(lists);

const step = ref('selection'); // destination, confirm
const $router = useRouter();
onBeforeRouteLeave(() => {
  $router.push({ name: 'IncomingList', params: { listKey: selectedItem.value.list_key } })
  selectedItem.value = undefined;
});
</script>
