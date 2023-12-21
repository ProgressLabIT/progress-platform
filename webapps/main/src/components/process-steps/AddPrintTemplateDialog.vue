<template>
  <!-- TODO: Create a better base component for using with custom dialog plugin components -->
  <BaseDialog
    :show="true"
    :get-dialog-ref="getDialogRef"
    :no-backdrop-dismiss="false"
    @close="onDialogHide"
  >
    <q-card square class="surface1" style="min-width: 400px">
      <q-card-section>
        <BaseAutocompleteTemplate
          :selected="selectedTemplates"
          @select="onDialogOK"
        />
      </q-card-section>
    </q-card>
  </BaseDialog>
</template>

<script setup>
import { useDialogPluginComponent } from 'quasar';
import BaseAutocompleteTemplate from '@/components/BaseAutocompleteTemplate.vue';
import BaseDialog from '@/components/BaseDialog.vue';

defineProps({
  selectedTemplates: {
    type: Array,
    default: () => [],
  },
});

defineEmits(useDialogPluginComponent.emitsObject);

const { dialogRef, onDialogHide, onDialogOK } = useDialogPluginComponent();
// This can't be inside the template due to unwrapping
// See: https://github.com/vuejs/composition-api/issues/317#issuecomment-1069145915
const getDialogRef = () => dialogRef;
</script>
