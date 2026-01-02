<template>
  <BaseModalForm
    :show="modelValue"
    :loading="loading"
    :handle-close="handleClose"
    @cancel="handleClose"
  >
    <template #title>
      {{ $t('warehouse.counting.import_records') }}
    </template>

    <template #form>
      <div class="column q-gutter-md">
        <!-- File Drop Area -->
        <div
          class="drop-area"
          :class="{
            'drop-area--dragging': isDragging,
            'drop-area--disabled': loading || validationResult !== null,
            'drop-area--has-file': selectedFile
          }"
          @dragenter.prevent="handleDragEnter"
          @dragover.prevent="handleDragOver"
          @dragleave.prevent="handleDragLeave"
          @drop.prevent="handleDrop"
          @click="openFilePicker"
        >
          <input
            ref="fileInput"
            type="file"
            accept=".csv,.xlsx"
            class="hidden"
            @change="handleFileSelect"
          />

          <template v-if="selectedFile">
            <q-icon name="mdi-file-check" size="48px" color="positive" />
            <div class="text-subtitle1 q-mt-sm">{{ selectedFile.name }}</div>
            <div class="text-caption text-grey">
              {{ formatFileSize(selectedFile.size) }}
            </div>
            <q-btn
              flat
              round
              size="sm"
              icon="mdi-close"
              color="negative"
              class="drop-area__clear"
              @click.stop="clearFile"
            />
          </template>
          <template v-else>
            <q-icon name="mdi-file-upload-outline" size="48px" color="grey-6" />
            <div class="text-subtitle1 text-grey-7 q-mt-sm">
              {{ $t('warehouse.counting.drop_file_here') }}
            </div>
            <div class="text-caption text-grey">
              {{ $t('warehouse.counting.or_click_to_browse') }}
            </div>
            <div class="text-caption text-grey q-mt-xs">
              .csv, .xlsx
            </div>
          </template>
        </div>

        <!-- Import Mode -->
        <div>
          <div class="text-subtitle2 q-mb-sm">{{ $t('warehouse.counting.import_mode') }}</div>
          <q-btn-toggle
            v-model="importMode"
            spread
            no-caps
            toggle-color="primary"
            :options="[
              { label: $t('warehouse.counting.import_mode_update'), value: 'update' },
              { label: $t('warehouse.counting.import_mode_replace'), value: 'replace' },
            ]"
            :disable="loading || validationResult !== null"
          />
          <div class="text-caption text-grey q-mt-xs">
            <template v-if="importMode === 'update'">
              {{ $t('warehouse.counting.import_mode_update_desc') }}
            </template>
            <template v-else>
              {{ $t('warehouse.counting.import_mode_replace_desc') }}
            </template>
          </div>
        </div>

        <!-- Replace Mode Warning -->
        <q-banner v-if="importMode === 'replace'" class="bg-orange-1 text-orange-9" rounded>
          <template #avatar>
            <q-icon name="mdi-alert" color="orange" />
          </template>
          {{ $t('warehouse.counting.replace_warning') }}
        </q-banner>

        <!-- Validation Result -->
        <template v-if="validationResult">
          <q-separator />

          <!-- Success State -->
          <div v-if="validationResult.status === 'valid'" class="q-pa-md bg-positive-1 rounded-borders">
            <div class="row items-center q-mb-sm">
              <q-icon name="mdi-check-circle" color="positive" size="md" class="q-mr-sm" />
              <span class="text-subtitle1 text-positive">{{ $t('warehouse.counting.validation_success') }}</span>
            </div>
            <div class="column q-gutter-xs text-body2">
              <div>
                <strong>{{ $t('warehouse.counting.rows_to_import') }}:</strong>
                {{ validationResult.records_to_add }}
              </div>
              <div v-if="validationResult.records_to_discard > 0">
                <strong>{{ $t('warehouse.counting.records_to_discard') }}:</strong>
                {{ validationResult.records_to_discard }}
              </div>
            </div>
          </div>

          <!-- Ignored Columns Warning -->
          <q-banner
            v-if="validationResult.status === 'valid' && validationResult.ignored_columns?.length > 0"
            class="bg-amber-1 text-amber-9"
            rounded
          >
            <template #avatar>
              <q-icon name="mdi-information" color="amber" />
            </template>
            {{ $t('warehouse.counting.ignored_columns_warning', { columns: validationResult.ignored_columns.join(', ') }) }}
          </q-banner>
        </template>

        <!-- Replace Confirmation Checkbox -->
        <q-checkbox
          v-if="validationResult?.status === 'valid' && importMode === 'replace'"
          v-model="replaceConfirmed"
          :label="$t('warehouse.counting.confirm_replace')"
          color="orange"
        />
      </div>
    </template>

    <template #actions>
      <div class="row full-width items-center q-gutter-md justify-end">
        <q-btn
          :label="$t('cancel')"
          color="theme-grey"
          flat
          @click="handleClose"
        />

        <!-- Validate Button -->
        <q-btn
          v-if="!validationResult"
          :label="$t('warehouse.counting.validate')"
          color="primary"
          :loading="loading"
          :disable="!selectedFile"
          @click="handleValidate"
        />

        <!-- Import Button -->
        <q-btn
          v-else-if="validationResult.status === 'valid'"
          :label="$t('warehouse.counting.import')"
          color="positive"
          :loading="loading"
          :disable="importMode === 'replace' && !replaceConfirmed"
          @click="handleImport"
        />

        <!-- Reset Button (after error) -->
        <q-btn
          v-else
          :label="$t('warehouse.counting.try_again')"
          color="primary"
          @click="resetValidation"
        />
      </div>
    </template>
  </BaseModalForm>
</template>

<script setup>
import { ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { Notify } from 'quasar';
import { api } from '@/boot/axios.js';
import BaseModalForm from '@/components/BaseModalForm.vue';

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
  sessionKey: {
    type: String,
    required: true,
  },
});

const emit = defineEmits(['update:modelValue', 'imported']);

const { t: $t } = useI18n();

// State
const loading = ref(false);
const selectedFile = ref(null);
const importMode = ref('update');
const validationResult = ref(null);
const replaceConfirmed = ref(false);
const isDragging = ref(false);
const fileInput = ref(null);

// Reset state when dialog opens
watch(
  () => props.modelValue,
  (isOpen) => {
    if (isOpen) {
      resetState();
    }
  }
);

function resetState() {
  selectedFile.value = null;
  importMode.value = 'update';
  validationResult.value = null;
  replaceConfirmed.value = false;
  loading.value = false;
}

function resetValidation() {
  validationResult.value = null;
  replaceConfirmed.value = false;
}

function clearFile() {
  selectedFile.value = null;
  validationResult.value = null;
  replaceConfirmed.value = false;
  if (fileInput.value) {
    fileInput.value.value = '';
  }
}

// Drag and drop handlers
function handleDragEnter() {
  if (loading.value || validationResult.value) return;
  isDragging.value = true;
}

function handleDragOver() {
  if (loading.value || validationResult.value) return;
  isDragging.value = true;
}

function handleDragLeave(e) {
  // Only set to false if we're leaving the drop area entirely
  if (!e.currentTarget.contains(e.relatedTarget)) {
    isDragging.value = false;
  }
}

function handleDrop(e) {
  isDragging.value = false;
  if (loading.value || validationResult.value) return;

  const files = e.dataTransfer?.files;
  if (files && files.length > 0) {
    const file = files[0];
    if (isValidFileType(file)) {
      selectedFile.value = file;
    } else {
      Notify.create({
        message: $t('warehouse.counting.invalid_file_type'),
        color: 'negative',
        position: 'top',
      });
    }
  }
}

function openFilePicker() {
  if (loading.value || validationResult.value) return;
  fileInput.value?.click();
}

function handleFileSelect(e) {
  const files = e.target.files;
  if (files && files.length > 0) {
    selectedFile.value = files[0];
  }
}

function isValidFileType(file) {
  const validTypes = ['.csv', '.xlsx'];
  const fileName = file.name.toLowerCase();
  return validTypes.some(type => fileName.endsWith(type));
}

function formatFileSize(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

function handleClose() {
  emit('update:modelValue', false);
}

async function handleValidate() {
  if (!selectedFile.value) return;

  loading.value = true;

  try {
    const formData = new FormData();
    formData.append('file', selectedFile.value);
    formData.append('count_session_key', props.sessionKey);
    formData.append('import_mode', importMode.value);
    formData.append('dry_run', 'true');

    const response = await api.post('/inventory/count-record/import', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      responseType: 'arraybuffer', // Handle both JSON and file responses
    });

    // Check if response is an error file (Excel)
    const contentType = response.headers['content-type'] || '';
    if (contentType.includes('spreadsheet') || contentType.includes('excel')) {
      // Download the error file
      const blob = new Blob([response.data], { type: contentType });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'import_errors.xlsx';
      link.click();
      window.URL.revokeObjectURL(url);

      // Get error count from headers
      const errorCount = response.headers['x-error-count'] || 'some';

      Notify.create({
        message: $t('warehouse.counting.validation_errors', { count: errorCount }),
        color: 'negative',
        position: 'top',
        timeout: 5000,
      });

      validationResult.value = { status: 'error' };
    } else {
      // Parse JSON response
      const textDecoder = new TextDecoder('utf-8');
      const jsonString = textDecoder.decode(response.data);
      const result = JSON.parse(jsonString);

      validationResult.value = result;

      Notify.create({
        message: $t('warehouse.counting.validation_success'),
        color: 'positive',
        position: 'top',
      });
    }
  } catch (error) {
    console.error('Validation error:', error);
    Notify.create({
      message: error.response?.data?.detail || $t('error'),
      color: 'negative',
      position: 'top',
    });
  } finally {
    loading.value = false;
  }
}

async function handleImport() {
  if (!validationResult.value?.file_key) return;

  loading.value = true;

  try {
    const formData = new FormData();
    formData.append('file_key', validationResult.value.file_key);
    formData.append('count_session_key', props.sessionKey);
    formData.append('import_mode', importMode.value);
    formData.append('dry_run', 'false');

    await api.post('/inventory/count-record/import', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    Notify.create({
      message: $t('warehouse.counting.import_success', {
        count: validationResult.value.records_to_add,
      }),
      color: 'positive',
      position: 'top',
    });

    emit('imported');
    handleClose();
  } catch (error) {
    console.error('Import error:', error);
    Notify.create({
      message: error.response?.data?.detail || $t('error'),
      color: 'negative',
      position: 'top',
    });
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped lang="sass">
.drop-area
  position: relative
  display: flex
  flex-direction: column
  align-items: center
  justify-content: center
  padding: 32px 24px
  border: 2px dashed var(--theme-grey)
  border-radius: 8px
  background: var(--q-grey-2)
  cursor: pointer
  transition: all 0.2s ease
  min-height: 160px

  &:hover:not(.drop-area--disabled)
    border-color: var(--q-primary)
    background: rgba(var(--q-primary-rgb), 0.05)

  &--dragging
    border-color: var(--q-primary)
    background: rgba(var(--q-primary-rgb), 0.1)
    border-style: solid

  &--disabled
    opacity: 0.6
    cursor: not-allowed

  &--has-file
    border-color: var(--q-positive)
    background: rgba(var(--q-positive-rgb), 0.05)
    border-style: solid

  &__clear
    position: absolute
    top: 8px
    right: 8px

.hidden
  display: none
</style>
