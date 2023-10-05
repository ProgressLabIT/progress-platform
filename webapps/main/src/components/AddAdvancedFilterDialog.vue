<template>
  <q-dialog ref="dialogRef" @hide="onDialogHide">
    <q-card class="dialog-card q-pa-lg surface2">
      <q-form id="filter-form" @submit="onDialogOK(formField)">
        <!-- TODO: -->

        <q-card-actions align="between" class="q-mt-md">
          <q-btn
            flat
            color="theme-grey"
            size="xl"
            :label="t('cancel')"
            @click="onDialogCancel"
          />

          <q-btn
            type="submit"
            form="filter-form"
            color="primary"
            size="xl"
            :label="t('confirm')"
          />
        </q-card-actions>
      </q-form>
    </q-card>
  </q-dialog>
</template>

<script setup>
import { useDialogPluginComponent } from 'quasar'
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'

defineEmits(useDialogPluginComponent.emitsObject)

const { dialogRef, onDialogHide, onDialogCancel, onDialogOK } = useDialogPluginComponent()

const { t } = useI18n()

const formField = ref(null)
</script>

<style lang="scss" scoped>
.dialog-card {
  min-width: 650px;
  max-width: 800px;
}
</style>
