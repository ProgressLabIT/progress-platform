<template>
  <SettingsSection
    v-slot="{ editMode }"
    :title="$t('views.companyDetails')"
    @cancel="cancel"
    @save="save"
  >
    <q-input
      v-if="editMode"
      v-model="configModel.companyName"
      :label="$t('settings.companyName')"
      filled
    />
    <div v-else class="text-h3 highlight">
      {{ configModel.companyName }}
    </div>

    <div class="q-mt-md">
      <div v-if="editMode" class="q-ml-xs q-pl-sm text-body2 text-low">
        {{ $t('settings.companyLogo.label') }}
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
      </div>
      <div v-if="editMode" class="low-text q-pt-xs">
        {{ $t('settings.companyLogo.hint', { size: logoSize }) }}
      </div>
    </div>
  </SettingsSection>
</template>

<script setup>
import { cloneDeep } from 'lodash';
import { onUnmounted, ref } from 'vue';
import SettingsSection from '@/components/SettingsSection.vue';
import { useConfigStore } from '@/stores/config';

const filePickerRef = ref();

const { config, configDefaults, updateAppConfig } = useConfigStore();

const configModel = ref(cloneDeep(config));
function cancel() {
  configModel.value = cloneDeep(config);
  logoUrl.value = config.companyLogo;
  logoFile.value = undefined;
}
async function save() {
  await updateAppConfig({
    companyName: configModel.value.companyName,
    companyLogo: logoFile.value,
  });
}

const logoUrl = ref(config.companyLogo);
// undefined: no change, null: restore default, otherwise: new file
const logoFile = ref();

onUnmounted(() => {
  URL.revokeObjectURL(logoUrl.value);
});

function onFilePicked(file) {
  logoFile.value = file;
  logoUrl.value = URL.createObjectURL(file);
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

  &--editable:hover &__avatar::before,
  &--editable:hover &__actions {
    opacity: 1;
  }
}
</style>
