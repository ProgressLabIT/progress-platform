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
          Movimenti completati
        </div>
        <div class="text-right text-body1">
          {{ movements.filter(m => m.status === 'completed').length }} / {{  movements.length }}
        </div>
      </div>
    </div>

    <q-scroll-area class="col q-my-md">

    <q-card
      v-for="m in movements"
      :key="m._key"
      class="surface1 q-pa-md q-mb-xs row justify-between items-baseline text-body1"
      :class="m.status === 'completed' ? 'theme-green' : 'surface1'"
    >

      <div>
        {{ m.product_code }}
      </div>
      <div v-if="m.serial_code">
        <span>
          # {{ m.serial_code }}
        </span>
      </div>
      <div v-else>
        {{ m.qt_planned - m.qt_completed }} / {{ m.qt_planned }}
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
  </q-page>
</template>

<script setup>
// import { ref } from 'vue';
import { useListsStore } from 'stores/lists';
import { useI18n } from 'vue-i18n';

const lists = useListsStore();
const { t: $t } = useI18n();

const props = defineProps({
  listKey: String
});

const list = lists.headers.find(l => l._key == props.listKey);
const movements = lists.movements[props.listKey];

</script>
