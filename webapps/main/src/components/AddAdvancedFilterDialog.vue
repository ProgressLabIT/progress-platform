<template>
  <q-dialog ref="dialogRef" @hide="onDialogHide">
    <q-card class="dialog-card q-pa-lg surface2">
      <q-form id="filter-form" @submit="onDialogOK(formField)">
        <q-card-section>
          <BaseAutocompleteCustomField
            v-model="customField"
            :label="capitalize(t('field'))"
            class="input-field"
            autofocus
            :rules="[(value) => !!value || t('field_required_alert')]"
          />
        </q-card-section>

        <q-card-section v-if="customField">
          <q-checkbox
            v-if="formField.type === 'files'"
            v-model="formField.value"
            :label="t('has_attachments')"
          />
          <FormField
            v-else
            :field="formField"
            class="input-field"
            @update="
              formField.value =
                formField.type === 'choice' ? $event?.value : $event
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
import { uid, useDialogPluginComponent } from 'quasar';
import { ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { capitalize } from 'boot/filters';
import BaseAutocompleteCustomField from './BaseAutocompleteCustomField.vue';
import FormField from './FormField.vue';

defineEmits(useDialogPluginComponent.emitsObject);

const { dialogRef, onDialogHide, onDialogCancel, onDialogOK } =
  useDialogPluginComponent();

const { t } = useI18n();

const formField = ref(null);

const customField = ref(null);
watch(customField, (customField) => {
  const value = ['boolean', 'files'].includes(customField.type) ? false : null;
  formField.value = {
    _key: uid(), // local-only
    custom_field_key: customField._key,
    label: customField.default_label,
    hint: customField.default_hint,
    value,
  };
});
</script>

<style lang="sass" scoped>
.dialog-card
  min-width: 400px
</style>
