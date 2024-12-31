<template>
  <q-page class="q-px-md q-pb-md q-py-sm column fit">


    <div class="row justify-between">
      <div class="col-auto">
        <div class="text-h5 text-low">
          {{ list.references.partner_name }}
        </div>
        <div class="text-h3">{{ list.code }}</div>
      </div>
      <div class="col-auto">
        <div class="text-h5 text-low">
          Righe completate
        </div>
        <div class="text-right text-body1">
          {{ listItems.filter(i => i.qt_planned === i.qt_confirmed).length }} / {{  listItems.length }}
        </div>
      </div>
    </div>

    <q-scroll-area class="col q-my-md">

    <q-card
      v-for="i in listItems"
      :key="i.product_code"
      class="surface1 q-pa-md q-mb-xs row items-center text-body1"
      :class="i.qt_planned === i.qt_completed ? 'theme-green' : 'surface1'"
      v-touch-hold.mouse="() => showItemReferences = i"
      @click.stop="() => selectedItem = i"
    >

      <div class="col-auto">
        <q-icon v-if="i.type === 'serial'" name="mdi-cube-scan" size="sm"/>
        <q-icon v-else name="mdi-apps" />
      </div>
      <div class="q-mx-md col-auto">
        <div class="text-h4 highlight">{{ i.product_code }}</div>
        <div class="smaller" style="line-height: 1rem;">{{ i.product_description }}</div>
        <div
          v-if="i.references.purchase_doc"
          class="text-h6 weight-bold uppercase q-mt-xs">
          {{ i.references.purchase_doc }}
        </div>
      </div>
      <q-space></q-space>
      <div>
        {{ i.qt_confirmed }} / {{ i.qt_planned }}
      </div>
    </q-card>
    </q-scroll-area>

    <div class="row q-col-gutter-x-sm">
      <div class="col-6">
        <q-btn
          color="theme-grey"
          :label="$t('back')"
          class="full-width"
          @click="$router.back()"
        />
      </div>
      <div class="col-6">
        <q-btn
          color="theme-green"
          :label="$t('save')"
          class="full-width"
          @click="null"
        />
      </div>
    </div>
    <q-btn
      color="theme-blue"
      :label="$t('complete')"
      class="full-width q-mt-sm"
      @click="null"
    />

    <SlideUpCard
      :model-value="showItemReferences !== false"
      @hide="() => showItemReferences=false"
    >
      <div class="text-h4 highlight q-mb-md">
        {{ showItemReferences.product_code }}
      </div>
      <div
        v-for="([ref, value]) in Object.entries(showItemReferences.references)"
        :key="ref"
      >
        {{ ref }}: <span class="highlight">{{ value }}</span>
      </div>
    </SlideUpCard>

    <SlideUpCard
      :model-value="selectedItem !== undefined"
      @hide="() => selectedItem = undefined"
      height="90vh">
      <ItemSerialsSelection v-if="selectedItem.type === 'serial'" :item="selectedItem" />
      <ItemQuantitySelection v-else :item="selectedItem" />
      <div class="col-auto q-mb-md">
        <q-btn
          color="theme-blue"
          :label="$t('print_label')"
          unelevated
          class="full-width"
          @click="printProductLabel(selectedItem.product_code, selectedItem.product_description)"
        />
      </div>
      <div class="col-auto row q-col-gutter-x-md">
        <div class="col-6">
          <q-btn
            class="full-width"
            color="theme-grey"
            :label="$t('cancel')"
            @click="() => selectedItem = undefined"
          />
        </div>
        <div class="col-6">
          <q-btn
            class="full-width"
            color="theme-blue"
            :label="$t('confirm')"
          />
        </div>
      </div>
    </SlideUpCard>
  </q-page>
</template>

<script setup>
import { ref } from 'vue';
import { useListsStore } from 'stores/lists';
import { useI18n } from 'vue-i18n';
import SlideUpCard from 'app/src/components/SlideUpCard.vue';
import ItemSerialsSelection from 'app/src/components/lists/ItemSerialsSelection.vue';
import ItemQuantitySelection from 'app/src/components/lists/ItemQuantitySelection.vue';
// import { QuantitySelector } from 'components/QuantitySelector.vue'
import { printProductLabel } from 'app/src/lib/print';


const lists = useListsStore();
const { t: $t } = useI18n();

const selectedItem = ref(undefined)
const showItemReferences = ref(false)
const props = defineProps({
  listKey: String
});

const list = lists.headers.find(l => l._key == props.listKey);
const listItems = lists.movementsByListAndProduct[props.listKey];
</script>
