<template>
  <div class="fit q-pa-md">
    <q-input
      v-if="editMode"
      v-model="configModel.companyName"
      label="Name"
      filled
      class="q-mb-md"
    />
    <div v-else class="text-h2 display q-pb-sm">
      {{ configModel.companyName }}
    </div>

    <div>
      <div v-if="editMode" class="q-ml-xs q-pl-sm text-body2 text-low">
        Logo
      </div>

      <div class="logo q-mt-sm" :class="{ 'logo--editable': editMode }">
        <q-img
          :src="logoUrl"
          class="logo__avatar"
          :width="logoSize"
          :height="logoSize"
          fit="contain"
        />

        <div v-if="editMode" class="logo__actions">
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
  </div>
</template>

<script setup>
import { onUnmounted, ref, watch } from 'vue';
import { useConfigStore } from '@/stores/config';

defineProps({
  editMode: {
    type: Boolean,
    required: true,
  },
});

const configModel = defineModel({ type: Object, required: true });

const filePickerRef = ref();

const { config, configDefaults } = useConfigStore();
const logoUrl = ref(config.companyLogo);
watch(
  () => config.companyLogo,
  (logo) => {
    logoUrl.value = logo;
  },
);
// in case the pending changes get cancelled
watch(
  () => configModel.value.companyLogo,
  (logo) => {
    if (typeof logo === 'string') {
      logoUrl.value = logo;
    }
  },
);

onUnmounted(() => {
  URL.revokeObjectURL(logoUrl.value);
});

function onFilePicked(file) {
  configModel.value.companyLogo = file;
  logoUrl.value = URL.createObjectURL(file);
}

function restoreDefaultLogo() {
  URL.revokeObjectURL(logoUrl.value);

  logoUrl.value = configDefaults.companyLogo;
  configModel.value.companyLogo = null;
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

  &--editable:hover &__avatar::before,
  &--editable:hover &__actions {
    opacity: 1;
  }
}
</style>
