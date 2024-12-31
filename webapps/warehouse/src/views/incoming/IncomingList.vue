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
      class="surface1 q-pa-md q-mb-xs row items-baseline text-body1"
      :class="i.qt_planned === i.qt_completed ? 'theme-green' : 'surface1'"
    >
      <q-icon v-if="i.type === 'serial'" name="mdi-cube-scan" />
      <q-icon v-else name="mdi-apps" />
      <div class="q-ml-md">
        {{ i.product_code }}
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

    <SlideUpCard :show="show">
      TEST
    </SlideUpCard>
  </q-page>
</template>

<script setup>
import { ref } from 'vue';
import { useListsStore } from 'stores/lists';
import { useI18n } from 'vue-i18n';
import SlideUpCard from 'app/src/components/SlideUpCard.vue';
// import { QuantitySelector } from 'components/QuantitySelector.vue'

const lists = useListsStore();
const { t: $t } = useI18n();

const show = ref(false)
const props = defineProps({
  listKey: String
});

const list = lists.headers.find(l => l._key == props.listKey);
const listItems = lists.movementsByListAndProduct[props.listKey];

</script>
