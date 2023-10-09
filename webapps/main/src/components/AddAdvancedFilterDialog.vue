<template>
  <q-dialog ref="dialogRef" @hide="onDialogHide">
    <q-card class="dialog-card q-pa-lg surface2">
      <q-form id="filter-form" @submit="onDialogOK(editableField)">
        <q-card-section>
          <BaseAutocompleteFormField
            v-model="formField"
            :label="capitalize(t('field'))"
            class="input-field"
            autofocus
            :rules="[value => !!value || t('field_required_alert')]"
          />
        </q-card-section>

        <q-card-section v-if="formField">
          <FormField
            :field_data="editableField"
            class="input-field"
            @update="editableField.value = $event"
          />
        </q-card-section>

        <q-card-actions align="between" class="q-mt-md">
          <q-btn
            color="theme-grey"
            padding="md xl"
            :label="t('cancel')"
            @click="onDialogCancel"
          />

          <q-btn
            type="submit"
            form="filter-form"
            color="primary"
            padding="md xl"
            :label="t('confirm')"
          />
        </q-card-actions>
      </q-form>
    </q-card>
  </q-dialog>
</template>

<script setup>
import { useDialogPluginComponent } from 'quasar'
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import BaseAutocompleteFormField from './BaseAutocompleteFormField.vue'
import { capitalize } from 'boot/filters'
import FormField from './FormField.vue'

defineEmits(useDialogPluginComponent.emitsObject)

const { dialogRef, onDialogHide, onDialogCancel, onDialogOK } = useDialogPluginComponent()

const { t } = useI18n()

const formField = ref(null)

const editableField = ref(null)
watch(formField, ({ default_label, default_hint, ...field }) => {
  editableField.value = {
    ...field,
    label: default_label,
    hint: default_hint,
    value: null
  }
})
</script>

<style lang="scss" scoped>
.dialog-card {
  min-width: 650px;
  max-width: 800px;
}

.input-field {
  :deep(.q-field__label) {
    height: 1em;
    font-size: 0.5em;
  }

  :deep(.q-field__prepend), :deep(.q-field__append) {
    height: 1.3em;
    font-size: 1.25em;
  }

  :deep(.q-field__control) {
    height: 1.75em;
    font-size: 4em;
    padding: 0.1em 0.3em;

    .q-field__native .q-field__input {
      height: 100%;
      padding-left: 0.25em;
    }
  }
}
</style>
