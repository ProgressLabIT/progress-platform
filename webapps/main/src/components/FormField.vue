<template>
  <div class="q-mb-lg">
    <!-- TEXT -->
    <q-input
      v-if="fieldType === 'text'"
      v-model="fieldValue"
      :disable="disable"
      :readonly="readonly"
      :dense="dense"
      label-slot
      filled
      stack-label
      autogrow
      input-debounce="100"
      hide-bottom-space
    >
      <template #label>
        {{ field.label ?? field.default_label }}
        <span v-if="field.mandatory" class="text-theme-red"> * </span>
      </template>
    </q-input>

    <!-- NUMBER -->
    <q-input
      v-if="fieldType === 'number'"
      v-model.number="fieldValue"
      type="number"
      :disable="disable"
      :dense="dense"
      label-slot
      filled
      stack-label
      hide-bottom-space
      input-debounce="100"
    >
      <template #label>
        {{ field.label ?? field.default_label }}
        <span v-if="field.mandatory" class="text-theme-red"> * </span>
      </template>
    </q-input>

    <!-- BOOLEAN -->
    <q-checkbox
      v-if="fieldType === 'boolean'"
      :model-value="fieldValue ?? false"
      :readonly="readonly"
      :disable="disable"
      :dense="dense"
      @update:model-value="fieldValue = $event"
    >
      {{ field.label ?? field.default_label }}
      <span v-if="field.mandatory" class="text-theme-red"> * </span>
    </q-checkbox>

    <!-- TERNARY -->
    <!-- TODO: Implement required behavior (?) -->
    <q-card
      v-if="fieldType === 'ternary'"
      square
      style="background: rgba(255, 255, 255, 0.07)"
      class="no-shadow"
      :class="dense ? 'q-px-md q-py-sm' : 'q-px-lg q-py-sm'"
    >
      <div class="row items-center">
        <div class="col-auto items-center">
          <q-avatar
            :color="fieldValue !== undefined ? 'theme-green' : 'transparent'"
            :size="dense ? '14px' : '20px'"
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

        <div class="col q-ml-md">
          <div>
            <span
              class="text-body2 q-ma-none"
              :class="{ smaller: dense, 'text-low': readonly, 'text-disabled': disable }"
            >
              {{ field.label ?? field.default_label }}
            </span>
            <span v-if="field.mandatory" class="text-theme-red q-ml-xs"> * </span>
          </div>
          <div
            class="smaller text-low"
            :class="{ smaller: dense, 'text-disabled': readonly || disable }"
          >
            {{ field.hint ?? field.default_hint }}
          </div>
        </div>

        <q-space />

        <div class="col-auto">
          <q-btn
            size="lg"
            unelevated
            :flat="fieldValue !== false"
            :disable="disable"
            :padding="dense ? 'sm md' : 'md lg'"
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
            color="theme-green"
            :style="{ width: dense ? '70px' : '100px' }"
            :padding="dense ? 'sm md' : 'md lg'"
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
      :readonly="readonly"
      :dense="dense"
      label-slot
      :loading="loading"
      :debounce="300"
      use-input
      clearable
      filled
      stack-label
      input-class="cursor-pointer"
      @filter="onFilter"
    >
      <template #label>
        {{ field.label ?? field.default_label }}
        <span v-if="field.mandatory" class="text-theme-red"> * </span>
      </template>
    </q-select>

    <!-- DATE -->
    <q-input
      v-if="fieldType === 'date'"
      v-model="fieldValue"
      :disable="disable"
      :readonly="readonly"
      label-slot
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
      <template #label>
        {{ field.label ?? field.default_label }}
        <span v-if="field.mandatory" class="text-theme-red"> * </span>
      </template>
    </q-input>

    <!-- TIME -->
    <q-input
      v-if="fieldType === 'time'"
      v-model="fieldValue"
      :disable="disable"
      :readonly="readonly"
      label-slot
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
      <template #label>
        {{ field.label ?? field.default_label }}
        <span v-if="field.mandatory" class="text-theme-red"> * </span>
      </template>
    </q-input>

    <!-- FILES -->
    <div v-if="fieldType === 'files'">
      <FilesList
        :files="fieldValue"
        :root-path="`${rootPath}/${field._key}`"
        :label="field.label ?? field.default_label"
        :disable="disable || readonly"
        :mandatory="field.mandatory"
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
  readonly: {
    type: Boolean,
    default: false
  }
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
