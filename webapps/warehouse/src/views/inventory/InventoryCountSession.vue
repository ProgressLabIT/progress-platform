<template>
  <div class="col column q-mt-md">
    <div class="text-h5 text-low text-uppercase">{{ t('count_session') }}</div>
    <div class="text-h3">{{ countingStore.sessionData?.code }}</div>
    <div class="text-body2 text-low">{{ countingStore.sessionData?.description }}</div>

    <!-- Product-based counting -->
    <CountingProductList
      v-if="countingStore.sessionData?.type === 'product'"
      :session-data="countingStore.sessionData"
      class="col q-mt-md"
    />

    <!-- Position-based counting -->
    <CountingPositionBrowser
      v-if="countingStore.sessionData?.type === 'position'"
      :session-data="countingStore.sessionData"
      class="col q-mt-md"
    />
  </div>
</template>

<script setup>
import { onMounted } from 'vue';
import { onBeforeRouteLeave } from 'vue-router';
import { useNavStore } from 'src/stores/navigation';
import { useCountingStore } from 'src/stores/counting';
import { useI18n } from 'vue-i18n';
import CountingProductList from '@/components/counting/CountingProductList.vue';
import CountingPositionBrowser from '@/components/counting/CountingPositionBrowser.vue';

const props = defineProps({
  countSessionKey: {
    type: String,
    required: true
  }
});

const { t } = useI18n();
const countingStore = useCountingStore();
const nav = useNavStore();

onMounted(async () => {
  await countingStore.loadCountSessionData(props.countSessionKey);
  nav.dynamicBreadcrumb = [countingStore.sessionData?.code]
})


onBeforeRouteLeave(() => {
  nav.dynamicBreadcrumb = []
  countingStore.resetCounting()
})


</script>

<style lang="scss" scoped>

</style>
