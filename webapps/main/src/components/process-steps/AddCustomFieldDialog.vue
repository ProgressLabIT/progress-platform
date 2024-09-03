<template>
  <!-- TODO: Create a better base component for using with custom dialog plugin components -->
  <BaseDialog
    :show="true"
    :get-dialog-ref="getDialogRef"
    :no-backdrop-dismiss="false"
    @close="onDialogHide"
  >
    <FormFieldSearch @select="onDialogOK" :excludeKeys="excludeKeys" />
  </BaseDialog>
</template>

<script setup>
import { useDialogPluginComponent } from 'quasar';
import BaseDialog from '@/components/BaseDialog.vue';
import FormFieldSearch from '@/components/FormFieldSearch.vue';

defineEmits(useDialogPluginComponent.emitsObject);
defineProps({ excludeKeys: { type: Array, default: () => [] } });
const { dialogRef, onDialogHide, onDialogOK } = useDialogPluginComponent();
// This can't be inside the template due to unwrapping
// See: https://github.com/vuejs/composition-api/issues/317#issuecomment-1069145915
const getDialogRef = () => dialogRef;
</script>
