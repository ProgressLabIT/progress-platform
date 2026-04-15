<template>
  <div class="q-pa-md column full-height">
    <div class="text-h6 q-mb-md col-auto">
      {{ isNew ? $t('new') : record_key }}
    </div>

    <!-- Key (editable only on create) -->
    <div class="col-auto">
    <q-input
      v-if="isNew"
      v-model="form.key"
      dense
      filled
      class="q-mb-md"
      :label="$t('custom_data.key')"
      :rules="[validateKey]"
      :hint="`a-z, 0-9, _ — max ${KEY_MAX_LENGTH} chars`"
      lazy-rules
    />
    </div>

    <!-- Description -->
    <div class="col-auto">
    <q-input
      v-model="form.description"
      dense
      filled
      class="q-mb-md"
      :label="$t('description')"
      type="textarea"
      autogrow
    />
    </div>

    <!-- JSON Value -->
    <div class="col">
      <JsonEditor
        v-model="form.value_str"
        :label="`${$t('value')} (JSON)`"
        :rows="15"
        @validation-error="json_has_error = $event"
      />
    </div>

    <BasePrompt
      :show="show_copy_prompt"
      :prompt="$t('custom_data.copy_value')"
      :help-text="$t('custom_data.new_key_prompt')"
      :initial_value="''"
      :require-change="false"
      @close="show_copy_prompt = false"
      @update="doCopy"
    />

    <!-- Actions -->
    <div class="row q-mt-md q-gutter-sm col-auto">
      <q-btn
        color="theme-blue"
        :label="$t('save')"
        :disable="!canSave"
        :loading="saving"
        @click="save"
      />
      <q-btn
        v-if="!isNew"
        outline
        color="theme-blue"
        :label="$t('custom_data.copy_value')"
        icon="mdi-content-copy"
        @click="show_copy_prompt = true"
      />
      <q-space />
      <q-btn
        v-if="!isNew"
        flat
        color="negative"
        :label="$t('delete')"
        @click="confirmDelete"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import { useRouter } from 'vue-router';
import { useQuasar } from 'quasar';
import { api } from '@/boot/axios.js';
import JsonEditor from '@/components/JsonEditor.vue';
import BasePrompt from '@/components/BasePrompt.vue';

const KEY_PATTERN = /^[a-z][a-z0-9_]*$/;
const KEY_MAX_LENGTH = 64;

const props = defineProps({
  record: {
    type: Object,
    default: null,
  },
});

const emit = defineEmits(['reload']);

const router = useRouter();
const $q = useQuasar();

const isNew = computed(() => !props.record);

const record_key = computed(() => props.record?._key || '');

const form = ref({
  key: '',
  description: '',
  value_str: '{}',
});

const json_has_error = ref(false);
const saving = ref(false);
const show_copy_prompt = ref(false);

// Populate form when record changes
watch(
  () => props.record,
  (rec) => {
    if (rec) {
      form.value = {
        key: rec._key,
        description: rec.description || '',
        value_str: JSON.stringify(rec.value, null, 2),
      };
    } else {
      form.value = { key: '', description: '', value_str: '{}' };
    }
  },
  { immediate: true },
);

function validateKey(val) {
  if (!val) return 'Key is required';
  if (val.length > KEY_MAX_LENGTH) return `Max ${KEY_MAX_LENGTH} characters`;
  if (!KEY_PATTERN.test(val)) return 'Lowercase letters, digits, underscores only. Must start with a letter.';
  return true;
}

const canSave = computed(() => {
  if (json_has_error.value) return false;
  if (isNew.value && validateKey(form.value.key) !== true) return false;
  return true;
});

async function save() {
  const key = isNew.value ? form.value.key : props.record._key;
  saving.value = true;

  try {
    const payload = {
      value: JSON.parse(form.value.value_str),
      description: form.value.description || null,
    };
    await api.put(`custom-data/${key}`, payload);

    $q.notify({ message: `Saved ${key}`, color: 'theme-green' });
    emit('reload');

    if (isNew.value) {
      router.push({ name: 'customDataDetail', params: { data_key: key } });
    }
  } catch (e) {
    $q.notify({ message: e.response?.data?.detail || e.message, color: 'theme-red' });
  } finally {
    saving.value = false;
  }
}

async function doCopy(newKey) {
  if (!newKey || !KEY_PATTERN.test(newKey) || newKey.length > KEY_MAX_LENGTH) {
    $q.notify({ message: validateKey(newKey), color: 'theme-red' });
    return;
  }
  show_copy_prompt.value = false;

  try {
    const payload = {
      value: JSON.parse(form.value.value_str),
      description: form.value.description || null,
    };
    await api.put(`custom-data/${newKey}`, payload);
    $q.notify({ message: `Created ${newKey}`, color: 'theme-green' });
    emit('reload');
    router.push({ name: 'customDataDetail', params: { data_key: newKey } });
  } catch (e) {
    $q.notify({ message: e.response?.data?.detail || e.message, color: 'theme-red' });
  }
}

function confirmDelete() {
  $q.dialog({
    title: 'Delete',
    message: `Delete "${props.record._key}"?`,
    cancel: true,
    persistent: true,
  }).onOk(async () => {
    try {
      await api.delete(`custom-data/${props.record._key}`);
      $q.notify({ message: 'Deleted', color: 'theme-green' });
      emit('reload');
      router.push({ name: 'customDataLibrary' });
    } catch (e) {
      $q.notify({ message: e.response?.data?.detail || e.message, color: 'theme-red' });
    }
  });
}
</script>
