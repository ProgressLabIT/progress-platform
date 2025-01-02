<template>
  <SlideUpCard
    :model-value="lists.selectedItem !== undefined"
    height="95vh"
    @hide="close"
  >

    <!-- ITEM SELECTION (QUANTITY / SERIALS)-->
    <template v-if="step==='selection'">
      <ItemSerialsSelection v-if="lists.selectedItem.type === 'serial'" />
      <ItemQuantitySelection v-else />

      <q-btn
        color="theme-blue"
        :label="$t('print_label')"
        unelevated
        class="full-width"
        @click="printProductLabel(lists.selectedItem.product_code, lists.selectedItem.product_description)"
      />
      <q-btn
        color="theme-blue"
        :label="$t('next')"
        :disable="lists.selectedItem.qt_confirmed === 0"
        unelevated
        class="full-width q-mt-md"
        @click="step = 'destination'"
      />
    </template>

    <!-- DESTINATION -->
    <template v-else-if="step==='destination'">
      <ItemPosition v-model="positionsTo" @next="() => step = 'confirm'" />
      <div class="row q-mt-md">
        <div class="col">
          <q-btn
            color="theme-grey"
            :label="$t('back')"
            unelevated
            class="full-width"
            @click="() => step = 'selection'"
          />
        </div>
        <div class="q-mx-sm"></div>
        <div class="col">
          <q-btn
            color="theme-blue"
            :label="$t('next')"
            unelevated
            class="full-width"
            @click="() => step = 'confirm'"
          />
        </div>
      </div>
    </template>

    <template v-else>
      <ItemConfirmation />
    </template>


  </SlideUpCard>
</template>

<script setup>
import { ref } from 'vue';
import { useI18n } from 'vue-i18n';
import SlideUpCard from 'app/src/components/SlideUpCard.vue';
import ItemQuantitySelection from 'app/src/components/lists/ItemQuantitySelection.vue';
import ItemSerialsSelection from 'app/src/components/lists/ItemSerialsSelection.vue';
import ItemPosition from 'app/src/components/lists/ItemPosition.vue';
import { printProductLabel } from 'app/src/lib/print';
import { useListsStore } from 'stores/lists';

const lists = useListsStore();
const { t: $t } = useI18n();


const close = () => {
  lists.selectedItem = undefined;
};

const step = ref('selection'); // destination, confirm
const positionsTo = ref([]);
</script>
