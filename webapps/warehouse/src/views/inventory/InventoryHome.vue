<template>
  <div class="col column q-gutter-y-md scroll">
    <div class="text-h1">{{ t('count_session', 2) }}</div>

    <q-card
      v-for="countSession in countSessions"
      :key="countSession._key"
      outlined
      class="surface2 q-pa-md"
      @click="router.push({ name: 'InventoryCountSession', params: { countSessionKey: countSession._key }})"
    >
      <div class="text-h3">{{ countSession?.code }}</div>
      <div class="text-subtitle2 text-low">{{ countSession?.description }}</div>
      <div class="row q-gutter-sm q-mt-sm">
        <q-chip :color="statusColor(countSession)" text-color="white">
          {{ countSession?.status }}
        </q-chip>
        <q-chip v-if="countSession.type" outline>
          {{ countSession?.type }}
        </q-chip>
      </div>
      <div v-if="countSession?.due_by" class="text-caption q-mt-sm">
        {{ t('due_by') }}: {{ shortDateString(countSession?.due_by) }}
      </div>
    </q-card>
    <q-space></q-space>

    <div class="text-h1">{{ t('inventory_checks') }}</div>

    <div class="row q-col-gutter-x-sm">
      <div class="col-4">
        <q-btn
          class="full-width"
          color="theme-blue"
          :label="t('product')"
          @click="router.push({ name: 'InventoryProduct' })"
        />
      </div>
      <div class="col-4">
        <q-btn
          class="full-width"
          color="theme-green"
          :label="t('serial', 2)"
          @click="router.push({ name: 'InventorySerial' })"
        />
      </div>
      <div class="col-4">
        <q-btn
          class="full-width"
          color="theme-grey"
          :label="t('position')"
          @click="router.push({ name: 'InventoryPosition' })"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { api } from 'src/boot/axios';
import { shortDateString } from 'src/lib/TimeHandling';

const { t } = useI18n();
const router = useRouter();

const countSessions = ref([]);

const statusColor = (session) => {
  if (!countSessions.value) {
    return 'grey';
  }

  switch (session.status) {
    case 'started': return 'theme-blue';
    case 'completed': return 'theme-green';
    case 'planned': return 'grey';
    case 'applied': return 'theme-green';
    case 'canceled': return 'theme-red';
    default: return 'grey';
  }
};

onMounted(async () => {
  try {
    const response = await api.get('/inventory/count-session', {
      params: {
        status: 'started'
      }
    });
    if (response.data && response.data.length > 0) {
      countSessions.value = response.data
    }
  } catch (error) {
    console.error('Error fetching count session:', error);
  }
});

</script>
