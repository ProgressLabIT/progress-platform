<template>
  <div class="q-mb-lg">
    <!-- TEXT -->
    <q-input
      v-if="fieldType === 'text'"
      v-model="fieldValue"
      :disable="disable"
      :dense="dense"
      :label="field.label ?? field.default_label"
      filled
      stack-label
      autogrow
      lazy-rules
      input-debounce="100"
      hide-bottom-space
      :rules="[
        (value) =>
          (field.required ? !!value : true) || $t('field_required_alert'),
      ]"
    />

    <!-- NUMBER -->
    <q-input
      v-if="fieldType === 'number'"
      v-model.number="fieldValue"
      type="number"
      :disable="disable"
      :dense="dense"
      :label="field.label ?? field.default_label"
      filled
      stack-label
      hide-bottom-space
      input-debounce="100"
      lazy-rules
      :rules="[
        (value) =>
          (field.required ? !!value : true) || $t('field_required_alert'),
      ]"
    />

    <!-- BOOLEAN -->
    <q-checkbox
      v-if="fieldType === 'boolean'"
      :model-value="fieldValue ?? false"
      :disable="disable"
      :dense="dense"
      :label="field.label"
      :rules="[
        (value) =>
          (field.required ? !!value : true) || $t('field_required_alert'),
      ]"
      @update:model-value="fieldValue = $event"
    />

    <!-- TERNARY -->
    <!-- TODO: Implement required behavior (?) -->
    <q-card
      v-if="fieldType === 'ternary'"
      square
      style="background: rgba(255, 255, 255, 0.07)"
      class="no-shadow"
      :class="dense ? 'q-px-md q-py-sm' : 'q-px-lg q-py-md'"
    >
      <div class="row items-center">
        <div class="col-1 items-center">
          <q-avatar
            :color="fieldValue !== undefined ? 'theme-green' : 'transparent'"
            size="24px"
            class="row flex-center text-center text-body2 font-weight-medium"
          >
            <q-icon
              v-if="fieldValue === undefined"
              size="sm"
              name="mdi-progress-question"
            />
            <q-icon v-else class="solid-white" name="mdi-check" />
          </q-avatar>
        </div>

        <div class="col items-center">
          <p class="text-body1 q-ma-none">
            {{ field.label ?? field.default_label }}
          </p>
        </div>

        <q-space />

        <div class="col-auto">
          <q-btn
            size="lg"
            unelevated
            :flat="fieldValue !== false"
            :disable="disable"
            :dense="dense"
            color="theme-red"
            :style="{ width: dense ? '70px' : '100px' }"
            @click="fieldValue = fieldValue === false ? undefined : false"
          >
            <span
              class="display weight-bold"
              :class="dense ? 'text-h5' : 'text-h4'"
            >
              {{ $t('no') }}
            </span>
          </q-btn>

          <q-btn
            size="lg"
            unelevated
            :flat="fieldValue !== true"
            :disable="disable"
            :dense="dense"
            color="theme-green"
            :style="{ width: dense ? '70px' : '100px' }"
            :class="dense ? 'q-ml-sm' : 'q-ml-lg'"
            @click="fieldValue = fieldValue === true ? undefined : true"
          >
            <span
              class="display weight-bold"
              :class="dense ? 'text-h5' : 'text-h4'"
            >
              {{ $t('yes') }}
            </span>
          </q-btn>
        </div>
      </div>
    </q-card>

    <!-- CHOICE -->
    <q-select
      v-if="fieldType === 'choice'"
      v-model="fieldValue"
      :options="options"
      option-label="value"
      :disable="disable"
      :dense="dense"
      :label="field.label ?? field.default_label"
      :loading="loading"
      :debounce="300"
      use-input
      clearable
      filled
      stack-label
      input-class="cursor-pointer"
      @filter="onFilter"
    />

    <!-- DATE -->
    <q-input
      v-if="fieldType === 'date'"
      v-model="fieldValue"
      :disable="disable"
      :label="field.label ?? field.default_label"
      filled
      stack-label
      :placeholder="$t('date_format')"
      input-class="cursor-pointer"
    >
      <template #append>
        <q-icon name="mdi-calendar" />
      </template>
      <q-popup-proxy anchor="center middle" self="center middle" @hide="blur">
        <q-date v-model="fieldValue" minimal>
          <div class="row items-center justify-end">
            <q-btn v-close-popup :label="$t('close')" color="primary" flat />
          </div>
        </q-date>
      </q-popup-proxy>
    </q-input>

    <!-- TIME -->
    <q-input
      v-if="fieldType === 'time'"
      v-model="fieldValue"
      :disable="disable"
      :label="field.label ?? field.default_label"
      stack-label
      filled
      input-class="cursor-pointer"
      placeholder="HH:mm"
    >
      <template #append>
        <q-icon name="mdi-clock-outline" />
      </template>
      <q-popup-proxy anchor="center middle" self="center middle" @hide="blur">
        <q-time v-model="fieldValue" format24h>
          <div class="row items-center justify-end">
            <q-btn v-close-popup :label="$t('close')" color="primary" flat />
          </div>
        </q-time>
      </q-popup-proxy>
    </q-input>

    <!-- FILES -->
    <div v-if="fieldType === 'files'">
      <FilesList
        :files="fieldValue"
        :root-path="`${rootPath}/${field._key}`"
        :label="field.label ?? field.default_label"
        :disable="disable"
        @add-files="addFiles"
        @delete-file="deleteFile"
        @restore-file="restoreFile"
      />
    </div>

    <div class="smaller q-px-sm q-mt-xs">
      {{ field.hint ?? field.default_hint }}
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { useStore } from 'vuex';
import { api } from '@/boot/axios';
import { capitalize } from '@/boot/filters';
import FilesList from '@/components/FilesList.vue';

const props = defineProps({
  field: {
    type:
      /** @type {import('vue').PropType<import('@/types/form').FormField>} */
      (Object),
    required: true,
  },
  rootPath: {
    type: String,
    default: undefined,
  },
  dense: {
    type: Boolean,
    default: false,
  },
  disable: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(['update']);

const fieldValue = computed({
  get: () => props.field.value,
  set(value) {
    emit('update', value);
  },
});

const { t } = useI18n();
const store = useStore();

const loading = ref(false);
const options = ref([]);
async function getOptions(searchTerm) {
  loading.value = true;
  const { data } = await api.get('list', {
    params: {
      field_key: props.field.custom_field_key ?? props.field._key,
      search: searchTerm || undefined,
    },
  });
  loading.value = false;
  return data;
}
async function onFilter(value, update, abort) {
  try {
    const optionsToLoad = await getOptions(value);
    update(() => {
      options.value = optionsToLoad;
    });
  } catch (error) {
    abort();
    console.error(error);
  }
}

const fieldType = computed(
  () =>
    store.getters.getCustomFieldByKey(
      props.field.custom_field_key ?? props.field._key,
    )?.type,
);
if (fieldType.value === 'choice') {
  void getOptions().then((optionsToLoad) => {
    options.value = optionsToLoad;
  });
}

function addFiles(fileList) {
  const existingFiles = fieldValue.value ?? [];
  for (const newFile of fileList) {
    const existingIndex = existingFiles.findIndex(
      ({ name }) => name === newFile.name,
    );
    if (existingIndex !== -1) {
      const shouldReplace = window.confirm(
        capitalize(
          t('product.alerts.doc_name_exists', 1, { filename: newFile.name }),
        ),
      );
      if (!shouldReplace) {
        return;
      }

      existingFiles.splice(existingIndex, 1);
    }

    existingFiles.push({
      content: newFile,
      name: newFile.name,
      temp: true,
      delete: false,
      // TODO: Revoke the object URL when needed
      path: URL.createObjectURL(newFile),
      size: newFile.size,
    });
  }
  fieldValue.value = existingFiles;
}

function deleteFile(index) {
  const file = fieldValue.value[index];
  if (file.temp) {
    fieldValue.value.splice(index, 1);
  } else {
    file.delete = true;
  }
}

function restoreFile(index) {
  fieldValue.value[index].delete = false;
}

function blur() {
  document.activeElement.blur();
}
</script>
