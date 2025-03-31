<template>
  <q-dialog ref="dialogRef" no-backdrop-dismiss no-shake @hide="onDialogHide">
    <q-card class="dialog-card q-pa-lg surface2">
      <q-card-section class="q-mb-md">
        <div
          class="text-h2 highlight text-center"
          style="font-family: 'Red Hat Display'"
        >
          {{ start_node.product_code }}
        </div>
      </q-card-section>
      <q-card-section>
        <BaseAutocompletePosition
          dense
          :load-data="false"
          :value="position.parent"
          @select="new_parent = $event._key"
        >
        </BaseAutocompletePosition>
      </q-card-section>
      <q-form id="position-form" @submit="save">
        <q-card-actions align="between" class="q-mt-md">
          <q-btn
            color="theme-grey"
            padding="md xl"
            :label="$t('cancel')"
            @click="onDialogCancel"
          />

          <q-btn
            type="submit"
            form="position-form"
            color="primary"
            padding="md xl"
            :label="$t('confirm')"
          />
        </q-card-actions>
      </q-form>
    </q-card>
  </q-dialog>
</template>

<script setup>
import { useDialogPluginComponent } from 'quasar';
import { ref } from 'vue';
import { useI18n } from 'vue-i18n';
import BaseAutocompletePosition from '@/components/BaseAutocompletePosition.vue';

const { t: $t } = useI18n({ useScope: 'global' });

const props = defineProps({
  node: {
    type: Object,
    required: true,
  },
  position: {
    type: Object,
    required: true,
  },
});

let start_node = ref(props.node);
let original = props.position.parent || 'IN';
let new_parent = ref(original);

defineEmits(useDialogPluginComponent.emitsObject);

const { dialogRef, onDialogHide, onDialogCancel, onDialogOK } =
  useDialogPluginComponent();

function save() {
  onDialogOK(new_parent.value);
}
</script>

<style lang="scss" scoped>
.dialog-card {
  min-width: 650px;
  max-width: 800px;
}

.number-input :deep(.q-field__control) {
  height: 1.25em;
  font-size: 6rem;

  .q-field__native {
    text-align: center;
  }
}
</style>
