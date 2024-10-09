<template>
  <SettingsSection
    v-slot="{ editMode }"
    :title="$t('views.apiTokenSettings')"
    :save-fn="() => {}"
    :hide-save="true"
    @cancel="cancel"
  >
    <APITokenLibrary
      :token_list="apiTokens"
      :edit-mode="editMode"
      dense
      @reload="loadTokens"
    />
  </SettingsSection>
</template>

<script setup>
import { onMounted, ref } from 'vue';
import { api } from '@/boot/axios';
import SettingsSection from '@/components/SettingsSection.vue';
import APITokenLibrary from '@/components/settings/APITokenLibrary.vue';

const apiTokens = ref([]);

async function cancel() {
  apiTokens.value = await getAPITokens();
}

onMounted(() => {
  loadTokens();
});

async function getAPITokens() {
  const { data } = await api.get('user/api-tokens');
  return data;
}

function loadTokens() {
  getAPITokens().then((data) => {
    apiTokens.value = data;
  });
}
</script>
