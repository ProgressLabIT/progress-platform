<template>
  <BaseDialog :show="true" :get-dialog-ref="getDialogRef" @close="onDialogHide">
    <q-card class="surface1 column" style="min-width: 420px; max-width: 90vw">
      <q-card-section class="display text-h5 col-auto">
        {{ $t('massCopyProcess.overwriteAlias.title') }}
      </q-card-section>

      <q-separator />

      <q-card-section>
        <div class="q-mb-md">
          {{ $t('massCopyProcess.overwriteAlias.message') }}
        </div>
        <q-checkbox
          v-model="overwrite"
          :label="$t('massCopyProcess.overwriteAlias.label')"
        />
      </q-card-section>

      <q-separator />

      <q-card-actions align="right">
        <q-btn
          flat
          color="theme-grey"
          :label="$t('cancel')"
          @click="onDialogCancel"
        />
        <q-btn
          :color="overwrite ? 'theme-orange' : 'theme-blue'"
          :label="$t('confirm')"
          @click="onDialogOK(overwrite)"
        />
      </q-card-actions>
    </q-card>
  </BaseDialog>
</template>

<script setup>
import { useDialogPluginComponent } from 'quasar';
import { ref } from 'vue';
import BaseDialog from '@/components/BaseDialog.vue';

defineEmits(useDialogPluginComponent.emitsObject);

const { dialogRef, onDialogHide, onDialogOK, onDialogCancel } =
  useDialogPluginComponent();
// This can't be inside the template due to unwrapping
// See: https://github.com/vuejs/composition-api/issues/317#issuecomment-1069145915
const getDialogRef = () => dialogRef;

const overwrite = ref(false);
</script>
