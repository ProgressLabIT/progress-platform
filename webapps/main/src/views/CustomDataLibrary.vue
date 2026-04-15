<template>
  <q-splitter v-model="splitter_model" class="absolute-full">
    <template #before>
      <div class="full-height column">
        <q-input
          v-model="search_text"
          dense
          filled
          class="q-px-md q-pt-md"
          :placeholder="$capitalize($t('search'))"
        >
          <template #append>
            <q-icon name="mdi-magnify" />
          </template>
        </q-input>

        <div
          class="row q-mt-md q-px-lg q-py-sm text-h6 text-uppercase weight-bold"
        >
          <div class="col">
            Key
          </div>
        </div>

        <q-separator />

        <q-scroll-area class="col">
          <div
            v-for="(item, index) in filtered_items"
            :key="item._key"
            class="row pointer q-px-lg q-py-xs medium overflow-hidden"
            :class="{
              'alternate-row': index % 2 === 0,
              'bg-blue-backdrop': item._key === selected_key,
            }"
            @click="showDetail(item._key)"
          >
            <div class="col ellipsis">
              {{ item._key }}
            </div>
            <div class="col ellipsis text-caption text-grey">
              {{ item.description }}
            </div>
          </div>
        </q-scroll-area>

        <q-separator />

        <div class="row flex-center smaller q-py-xs">
          {{ filtered_items.length }} {{ $t('of') }} {{ items.length }}
        </div>

        <div class="q-pa-md q-mt-auto">
          <q-btn
            class="full-width q-mt-auto"
            color="theme-blue"
            :label="$t('new')"
            @click="showNew"
          />
        </div>
      </div>
    </template>

    <template #after>
      <div class="col full-height">
        <router-view v-slot="{ Component, route }">
          <component
            :is="Component"
            v-if="route.name === 'customDataNew'"
            @reload="loadItems"
          />
          <component
            :is="Component"
            v-else-if="selected_record"
            :record="selected_record"
            @reload="loadItems"
          />
        </router-view>
      </div>
    </template>
  </q-splitter>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { api } from '@/boot/axios.js';
import multiMatch from '@/lib/MultiFieldSearch.js';

const route = useRoute();
const router = useRouter();

const search_text = ref(undefined);
const splitter_model = ref(30);
const items = ref([]);

const selected_key = computed(() => route.params.data_key);

const selected_record = computed(() => {
  const key = selected_key.value;
  if (!key) return undefined;
  return items.value.find((item) => item._key === key);
});

const filtered_items = computed(() => {
  return items.value.filter((item) =>
    multiMatch(search_text.value, item, ['_key', 'description']),
  );
});

async function loadItems() {
  try {
    const { data } = await api.get('custom-data');
    items.value = data;
  } catch (e) {
    items.value = [];
  }
}

function showDetail(data_key) {
  router.push({ name: 'customDataDetail', params: { data_key } });
}

function showNew() {
  router.push({ name: 'customDataNew' });
}

onMounted(loadItems);
</script>
