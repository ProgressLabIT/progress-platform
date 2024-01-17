<template>
  <div class="fit q-pa-md">
    <q-input v-model="companyName" label="Name" filled class="q-mb-md" />

    <div>
      <div class="q-ml-xs q-pl-sm text-body2 text-low">Logo</div>

      <div class="logo q-mt-sm">
        <q-img
          :src="logoUrl"
          class="logo__avatar"
          :width="logoSize"
          :height="logoSize"
          fit="contain"
        />

        <div class="logo__actions">
          <q-btn
            flat
            round
            icon="mdi-pencil"
            @click="filePickerRef.pickFiles()"
          />

          <q-btn
            v-if="logoUrl !== configDefaults.companyLogo"
            flat
            round
            icon="mdi-delete"
            color="negative"
            @click="restoreDefaultLogo"
          />
        </div>
        <q-file
          ref="filePickerRef"
          class="hidden"
          accept="image/*"
          @update:model-value="onFilePicked"
        />

        <!-- TODO: Add hint about size and format requirements -->
      </div>
    </div>

    <q-btn
      label="Save"
      color="theme-blue"
      class="full-width q-mt-md"
      @click="save"
    />
  </div>
</template>

<script setup>
import { onUnmounted, ref, watch } from 'vue';
import { useConfigStore } from '@/stores/config';

const filePickerRef = ref();

const { config, configDefaults, updateAppConfig } = useConfigStore();

watch(
  () => config,
  (config) => {
    companyName.value = config.companyName;
    logoUrl.value = config.companyLogo;
  },
  { deep: true },
);

const companyName = ref(config.companyName);
/** @type {import('vue').Ref<File | undefined | null>} */
const logoFile = ref();
const logoUrl = ref(config.companyLogo);

onUnmounted(() => {
  URL.revokeObjectURL(logoUrl.value);
});

function onFilePicked(file) {
  logoFile.value = file;
  logoUrl.value = URL.createObjectURL(file);
}

async function save() {
  await updateAppConfig({
    companyName: companyName.value,
    companyLogo: logoFile.value,
  });
}

function restoreDefaultLogo() {
  URL.revokeObjectURL(logoUrl.value);

  logoUrl.value = configDefaults.companyLogo;
  logoFile.value = null;
}

const logoSize = '300px';
</script>

<style scoped lang="scss">
.logo {
  position: relative;
  width: v-bind(logoSize);
  height: v-bind(logoSize);
  border: 1px solid var(--theme-grey);
  box-sizing: content-box;

  &__avatar::before {
    content: '';
    position: absolute;
    width: v-bind(logoSize);
    height: v-bind(logoSize);
    background-color: rgba(0, 0, 0, 0.54);

    transition: opacity 0.5s ease;
    opacity: 0;
    z-index: 1;
  }

  &__actions {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);

    transition: opacity 0.5s ease;
    opacity: 0;
    z-index: 2;
  }

  &:hover &__avatar::before,
  &:hover &__actions {
    opacity: 1;
  }
}
</style>
