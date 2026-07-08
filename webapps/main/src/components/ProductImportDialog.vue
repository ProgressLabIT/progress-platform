<template>
  <BaseModalForm
    :show="modelValue"
    :loading="loading"
    :handle-close="handleClose"
    @cancel="handleClose"
  >
    <template #title>
      {{ $t('product.import.dialog_title') }}
    </template>

    <template #form>
      <div class="column q-gutter-md import-form-body">
        <!-- File Drop Area -->
        <div
          class="drop-area"
          :class="{
            'drop-area--dragging': isDragging,
            'drop-area--disabled': loading || validationResult !== null,
            'drop-area--has-file': selectedFile,
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
            <q-icon name="mdi-file-check" size="48px" color="theme-green" />
            <div class="text-subtitle1 q-mt-sm">{{ selectedFile.name }}</div>
            <div class="text-caption text-grey">
              {{ formatFileSize(selectedFile.size) }}
            </div>
            <q-btn
              flat
              round
              size="sm"
              icon="mdi-close"
              class="drop-area__clear"
              :aria-label="$t('product.import.clear_file')"
              @click.stop="clearFile"
            />
          </template>
          <template v-else>
            <q-icon name="mdi-file-upload-outline" size="48px" color="grey-6" />
            <div class="text-subtitle1 text-grey-7 q-mt-sm">
              {{ $t('product.import.drop_file_here') }}
            </div>
            <div class="text-caption text-grey">
              {{ $t('product.import.or_click_to_browse') }}
            </div>
            <div class="text-caption text-grey q-mt-xs">.csv, .xlsx</div>
          </template>
        </div>

        <!-- Validation Result -->
        <template v-if="validationResult">
          <q-separator />

          <!-- VAL-04: Post-import summary panel (Phase 3) — shown when execute completes -->
          <div v-if="importResult" class="q-pa-md bg-green-backdrop rounded-borders">
            <div class="row items-center q-mb-sm">
              <q-icon name="mdi-check-circle" color="theme-green" size="md" class="q-mr-sm" />
              <span class="text-subtitle1 text-theme-green">{{
                $t('product.import.summary_title')
              }}</span>
            </div>
            <div class="column q-gutter-xs text-body2">
              <div>
                <strong>{{ $t('product.import.summary_created') }}:</strong>
                {{ importResult.created_count }}
              </div>
              <div>
                <strong>{{ $t('product.import.summary_updated') }}:</strong>
                {{ importResult.updated_count }}
              </div>
              <div>
                <strong>{{ $t('product.import.summary_skipped') }}:</strong>
                {{ importResult.skipped_count }}
              </div>
              <div v-if="importResult.errored_count > 0">
                <strong class="text-negative">{{ $t('product.import.summary_errored') }}:</strong>
                <span class="text-negative">{{ importResult.errored_count }}</span>
              </div>
              <div v-else>
                <strong>{{ $t('product.import.summary_errored') }}:</strong>
                {{ importResult.errored_count }}
              </div>
            </div>
          </div>

          <!-- Success State (shown during dry-run validation, before execute) -->
          <template v-else-if="validationResult.status === 'valid'">
            <!-- VAL-01: Per-row preview table (Phase 3) -->
            <div v-if="validationResult?.rows?.length" class="q-mt-sm">
              <div class="text-subtitle2 q-mb-sm">{{ $t('product.import.preview_title') }}</div>
              <q-table
                class="preview-table"
                style="max-height: calc(100vh - 624px); min-height: 120px"
                :rows="validationResult.rows"
                :columns="previewColumns"
                row-key="row"
                :pagination="{ rowsPerPage: 10 }"
                :rows-per-page-options="[10, 25, 50]"
                :rows-per-page-label="$t('product.import.preview_rows_per_page')"
                :pagination-label="paginationLabel"
                flat
                bordered
                :no-data-label="$t('product.import.preview_no_rows')"
              >
                <template #body-cell-action="slotProps">
                  <q-td :props="slotProps" class="text-center">
                    <q-badge
                      :color="actionColor(slotProps.row.action)"
                      :label="$t('product.import.action_' + slotProps.row.action)"
                      rounded
                    />
                  </q-td>
                </template>
              </q-table>
            </div>

            <!-- VAL-02: Per-row error list (Phase 3) — shown when rows have errors -->
            <div v-if="errorRows.length > 0" class="q-mt-sm">
              <div class="row items-center q-mb-xs">
                <q-icon name="mdi-alert-circle" color="negative" size="sm" class="q-mr-xs" />
                <span class="text-subtitle2 text-negative">
                  {{ $t('product.import.error_list_title', { count: errorRows.length }) }}
                </span>
              </div>
              <div style="max-height: 200px; overflow-y: auto">
                <q-list dense bordered separator>
                  <q-item v-for="row in errorRows" :key="row.row">
                    <q-item-section avatar>
                      <q-icon name="mdi-alert-circle" color="negative" size="sm" />
                    </q-item-section>
                    <q-item-section>
                      <q-item-label class="text-body2">Row {{ row.row }}: {{ row.code || '—' }}</q-item-label>
                      <q-item-label caption class="text-grey-7">{{ row.errors.join('; ') }}</q-item-label>
                    </q-item-section>
                  </q-item>
                </q-list>
              </div>
            </div>

            <!-- Aggregate counts panel (Phase 2, extended with skipped_count) -->
            <div class="q-pa-md bg-green-backdrop rounded-borders q-mt-sm">
              <div class="row items-center q-mb-sm">
                <q-icon
                  name="mdi-check-circle"
                  color="theme-green"
                  size="md"
                  class="q-mr-sm"
                />
                <span class="text-subtitle1 text-theme-green">{{
                  $t('product.import.validation_success')
                }}</span>
              </div>
              <div class="column q-gutter-xs text-body2">
                <div>
                  <strong>{{ $t('product.import.created_count') }}:</strong>
                  {{ validationResult.created_count }}
                </div>
                <div>
                  <strong>{{ $t('product.import.updated_count') }}:</strong>
                  {{ validationResult.updated_count }}
                </div>
              </div>
            </div>
          </template>

          <!-- Ignored Columns Warning -->
          <q-banner
            v-if="
              validationResult.status === 'valid' &&
              validationResult.ignored_columns?.length > 0
            "
            class="bg-amber-1 text-amber-9"
            rounded
          >
            <template #avatar>
              <q-icon name="mdi-information" color="amber" />
            </template>
            {{
              $t('product.import.ignored_columns_warning', {
                columns: validationResult.ignored_columns.join(', '),
              })
            }}
          </q-banner>
        </template>
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

        <!-- Phase 3: Close button in done state (importResult set after execute) -->
        <q-btn
          v-if="importResult"
          :label="$t('product.import.close')"
          color="theme-green"
          @click="handleClose"
        />

        <!-- Validate Button -->
        <q-btn
          v-else-if="!validationResult"
          :label="$t('product.import.validate')"
          color="primary"
          :loading="loading"
          :disable="!selectedFile"
          @click="handleValidate"
        />

        <!-- Import Button (VAL-03: disabled when any error rows present) -->
        <q-btn
          v-else-if="validationResult.status === 'valid'"
          :label="$t('product.import.import')"
          color="theme-green"
          :loading="loading"
          :disable="!validationResult || validationResult.status !== 'valid' || errorRows.length > 0"
          @click="handleImport"
        />
      </div>
    </template>
  </BaseModalForm>
</template>

<script setup>
import { Notify } from 'quasar';
import { ref, computed, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { api } from '@/boot/axios.js';
import BaseModalForm from '@/components/BaseModalForm.vue';

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(['update:modelValue', 'imported']);

const { t: $t } = useI18n();

// State
const loading = ref(false);
const selectedFile = ref(null);
const validationResult = ref(null);
const isDragging = ref(false);
const fileInput = ref(null);
const importResult = ref(null); // { created_count, updated_count, skipped_count, errored_count } | null

// Phase 3 computed
const errorRows = computed(() => validationResult.value?.rows?.filter((r) => r.action === 'error') ?? []);

// Computed so column labels re-resolve when the UI locale changes (a plain const
// would freeze the labels at setup-time locale, leaving the header untranslated).
const previewColumns = computed(() => [
  {
    name: 'row',
    field: 'row',
    label: $t('product.import.preview_col_row'),
    align: 'right',
    style: 'min-width: 64px',
  },
  {
    name: 'code',
    field: 'code',
    label: $t('product.import.preview_col_code'),
    align: 'left',
  },
  {
    name: 'action',
    field: 'action',
    label: $t('product.import.preview_col_action'),
    align: 'center',
    style: 'min-width: 120px',
  },
]);

// Quasar's q-table footer ("Records per page" / "1-10 of N") renders from the
// Quasar lang pack, not vue-i18n — wire it through $t so it follows the app locale.
function paginationLabel(firstRowIndex, endRowIndex, totalRowsNumber) {
  return $t('product.import.preview_pagination', {
    first: firstRowIndex,
    last: endRowIndex,
    total: totalRowsNumber,
  });
}

function actionColor(action) {
  const map = { create: 'theme-green', update: 'info', error: 'negative', skipped: 'warning' };
  return map[action] ?? 'grey';
}

// Reset state when dialog opens
watch(
  () => props.modelValue,
  (isOpen) => {
    if (isOpen) {
      resetState();
    }
  },
);

function resetState() {
  selectedFile.value = null;
  validationResult.value = null;
  loading.value = false;
  importResult.value = null; // Phase 3: prevents stale summary on reopen
}

function clearFile() {
  selectedFile.value = null;
  validationResult.value = null;
  if (fileInput.value) {
    fileInput.value.value = '';
  }
}

// Drag and drop handlers
function handleDragEnter() {
  if (loading.value || validationResult.value) {return;}
  isDragging.value = true;
}

function handleDragOver() {
  if (loading.value || validationResult.value) {return;}
  isDragging.value = true;
}

function handleDragLeave(e) {
  if (!e.currentTarget.contains(e.relatedTarget)) {
    isDragging.value = false;
  }
}

function handleDrop(e) {
  isDragging.value = false;
  if (loading.value || validationResult.value) {return;}

  const files = e.dataTransfer?.files;
  if (files && files.length > 0) {
    const file = files[0];
    if (isValidFileType(file)) {
      selectedFile.value = file;
    } else {
      Notify.create({
        message: $t('product.import.invalid_file_type'),
        color: 'negative',
        position: 'top',
      });
    }
  }
}

function openFilePicker() {
  if (loading.value || validationResult.value) {return;}
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
  return validTypes.some((type) => fileName.endsWith(type));
}

function formatFileSize(bytes) {
  if (bytes < 1024) {return bytes + ' B';}
  if (bytes < 1024 * 1024) {return (bytes / 1024).toFixed(1) + ' KB';}
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

function handleClose() {
  emit('update:modelValue', false);
}

async function handleValidate() {
  if (!selectedFile.value) {return;}

  loading.value = true;

  try {
    const formData = new FormData();
    formData.append('file', selectedFile.value);
    formData.append('dry_run', 'true');

    const response = await api.post('/product/import', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      responseType: 'arraybuffer',
    });

    // Check if response is an error file (Excel)
    const contentType = response.headers['content-type'] || '';
    if (contentType.includes('spreadsheet') || contentType.includes('excel')) {
      // Auto-download the annotated error file
      const blob = new Blob([response.data], { type: contentType });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'product_import_errors.xlsx';
      link.click();
      window.URL.revokeObjectURL(url);

      const errorCount = response.headers['x-error-count'] || 'some';

      Notify.create({
        message: $t('product.import.validation_errors', { count: errorCount }),
        color: 'negative',
        position: 'top',
        timeout: 5000,
      });

      // Reset to State 1 so user can upload the corrected file
      clearFile();
    } else {
      // Parse JSON success response
      const textDecoder = new TextDecoder('utf-8');
      const jsonString = textDecoder.decode(response.data);
      validationResult.value = JSON.parse(jsonString);

      Notify.create({
        message: $t('product.import.validation_success'),
        color: 'theme-green',
        position: 'top',
      });
    }
  } catch (error) {
    Notify.create({
      message: error.response?.data?.detail || $t('product.import.unexpected_error'),
      color: 'negative',
      position: 'top',
    });
  } finally {
    loading.value = false;
  }
}

async function handleImport() {
  if (!validationResult.value?.file_key) {return;}

  loading.value = true;

  try {
    const formData = new FormData();
    formData.append('file_key', validationResult.value.file_key);
    formData.append('dry_run', 'false');

    // Phase 3: capture execute response (NO responseType: 'arraybuffer' — always JSON)
    const response = await api.post('/product/import', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    const detail = response.data.detail;
    importResult.value = {
      created_count: detail.created ?? detail.created_count ?? 0,
      updated_count: detail.updated ?? detail.updated_count ?? 0,
      skipped_count: detail.skipped ?? detail.skipped_count ?? 0,
      errored_count: 0,
    };

    emit('imported');

    Notify.create({
      message: $t('product.import.import_success'),
      color: 'theme-green',
      position: 'top',
      timeout: 3000,
    });
    // Dialog stays open — user closes via summary panel "Close" button
  } catch (error) {
    Notify.create({
      message: error.response?.data?.detail || $t('product.import.unexpected_error'),
      color: 'negative',
      position: 'top',
    });
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped lang="sass">
// Keep the dialog body a single vertical stack. Quasar's .column is a
// wrapping flex column — with a height cap it would wrap children into
// side-by-side columns. nowrap forces one column; the preview table below
// owns the scrolling so the body itself never needs to overflow.
.import-form-body
  flex-wrap: nowrap

// The preview table is the only scroll region: a bounded max-height (set
// inline) makes q-table's middle scroll; the header row is pinned so column
// labels stay visible. Header background matches the card surface so rows
// don't bleed through while scrolling.
.preview-table :deep(thead tr th)
  position: sticky
  top: 0
  z-index: 1

[progress-theme='dark'] .preview-table :deep(thead tr th)
  background-color: #1f2a2d

[progress-theme='light'] .preview-table :deep(thead tr th)
  background-color: #fafafa

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
    border-color: var(--theme-green)
    background: rgba(13, 171, 118, 0.05)
    border-style: solid

  &__clear
    position: absolute
    top: 8px
    right: 8px

.hidden
  display: none
</style>
