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
            :rules="[(value) => !!value || t('field_required_alert')]"
          />
        </q-card-section>

        <q-card-section v-if="formField">
          <q-checkbox
            v-if="editableField.type === 'files'"
            v-model="editableField.value"
            :label="t('has_attachments')"
          >
          </q-checkbox>
          <FormField
            v-else
            :field="editableField"
            class="input-field"
            @update="
              editableField.value =
                editableField.type === 'choice' ? $event?.value : $event
            "
          />
        </q-card-section>

        <q-card-actions align="between" class="q-px-md">
          <q-btn
            color="theme-grey"
            :label="t('cancel')"
            @click="onDialogCancel"
          />

          <q-btn
            type="submit"
            form="filter-form"
            color="primary"
            :label="t('confirm')"
          />
        </q-card-actions>
      </q-form>
    </q-card>
  </q-dialog>
</template>

<script setup>
import { useDialogPluginComponent } from 'quasar';
import { ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { capitalize } from 'boot/filters';
import BaseAutocompleteFormField from './BaseAutocompleteFormField.vue';
import FormField from './FormField.vue';

defineEmits(useDialogPluginComponent.emitsObject);

const { dialogRef, onDialogHide, onDialogCancel, onDialogOK } =
  useDialogPluginComponent();

const { t } = useI18n();

const formField = ref(null);

const editableField = ref(null);

watch(formField, ({ default_label, default_hint, ...field }) => {
  const value = ['boolean', 'files'].includes(field.type) ? false : null;
  editableField.value = {
    ...field,
    label: default_label,
    hint: default_hint,
    value,
  };
});
</script>

<style lang="sass" scoped>
.dialog-card
  min-width: 400px
</style>
