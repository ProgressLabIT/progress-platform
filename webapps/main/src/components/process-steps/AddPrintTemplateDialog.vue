<template>
  <!-- TODO: Create a better base component for using with custom dialog plugin components -->
  <BaseDialog
    :show="true"
    :get-dialog-ref="getDialogRef"
    :no-backdrop-dismiss="false"
    @close="onDialogHide"
  >
    <EntityPicker
      :options="nonSelectedTemplates"
      :searchable-fields="['name', 'description']"
      @select="onDialogOK"
    >
      <template #item="{ item, itemProps }">
        <q-item v-bind="itemProps">
          <q-item-section>
            <q-item-label class="highlight">
              {{ item.name }}
            </q-item-label>

            <q-item-label caption lines="2">
              {{ item.description }}
            </q-item-label>
          </q-item-section>
        </q-item>
      </template>
    </EntityPicker>
  </BaseDialog>
</template>

<script setup>
import { useDialogPluginComponent } from 'quasar';
import { computed } from 'vue';
import BaseDialog from '@/components/BaseDialog.vue';
import EntityPicker from '@/components/EntityPicker.vue';
import { usePrintTemplates } from '@/composables/print-template';

const props = defineProps({
  selectedKeys: {
    type: Array,
    default: () => [],
  },
});

defineEmits(useDialogPluginComponent.emitsObject);

const { dialogRef, onDialogHide, onDialogOK } = useDialogPluginComponent();
// This can't be inside the template due to unwrapping
// See: https://github.com/vuejs/composition-api/issues/317#issuecomment-1069145915
const getDialogRef = () => dialogRef;

const { templates } = usePrintTemplates();

const nonSelectedTemplates = computed(() =>
  templates.value.filter(({ _key }) => !props.selectedKeys.includes(_key)),
);
</script>
