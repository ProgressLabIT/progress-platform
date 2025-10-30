<template>
  <div v-if="fieldsModel.length === 0" class="q-mt-md text-italic">
    {{ $t('field_none') }}
  </div>
  <div v-else id="form-template-fields" class="col scroll">
    <div
      v-for="(field, index) in fieldsModel"
      :key="field._key"
      class="row items-center q-col-gutter-lg q-py-sm"
    >
      <div class="col-auto">
        <q-icon
          v-if="isDragDropEnabled"
          name="mdi-drag-horizontal-variant"
          class="q-mr-sm drag-handle"
          size="sm"
        />
        <q-icon :name="getFieldIcon(field)" size="sm" />
      </div>

      <div class="col">
        <q-input
          v-model="field.label"
          autogrow
          :readonly="!editMode"
          :label="$t('label')"
          stack-label
          filled
          dense
        />
      </div>

      <div class="col">
        <q-input
          v-model="field.hint"
          autogrow
          :readonly="!editMode"
          :label="$t('hint')"
          stack-label
          filled
          dense
        />
      </div>

      <div class="col-auto" v-if="field.custom_field_key !== 'separator'">
        <q-toggle
          v-model="field.mandatory"
          :disable="!editMode"
          :label="$t('mandatory')"
        />
      </div>
      <div class="col-auto"></div>

      <div class="col-auto">
        <q-btn
          v-if="editMode"
          round
          flat
          icon="mdi-close"
          @click="deleteField(index)"
        />
      </div>
      <!-- TODO: default value and hidden -->
    </div>
  </div>

  <div class="row q-gutter-x-md">
    <q-btn
      v-if="editMode"
      size="sm"
      color="theme-blue"
      icon="mdi-plus"
      :label="$t('field_add')"
      class="q-mt-lg"
      @click="addField"
    />
    <q-btn
      v-if="editMode"
      size="sm"
      color="theme-blue"
      icon="mdi-ab-testing"
      :label="$t('separator_add')"
      class="q-mt-lg"
      @click="addSeparator"
    />
  </div>
</template>

<script setup>
import { Dialog, uid } from 'quasar';
import Sortable from 'sortablejs';
import { computed, nextTick, ref, watch } from 'vue';
import { useStore } from 'vuex';
import { useFormFields } from '@/composables/form';
import AddCustomFieldDialog from './process-steps/AddCustomFieldDialog.vue';

const props = defineProps({
  editMode: {
    type: Boolean,
    required: true,
  },
});

const fieldsModel = defineModel({ type: Array, required: true });

const store = useStore();

const { getFieldIcon: _getIcon } = useFormFields();
function getFieldIcon(field) {
  const customField = store.getters.getCustomFieldByKey(field.custom_field_key);
  return _getIcon(customField?.type);
}

const isDragging = ref(false);
/** @type {ReturnType<typeof Sortable.create> | undefined} */
let sortable;
function initSortable() {
  const container = document.querySelector('#form-template-fields');
  if (!container) {
    return;
  }

  sortable = Sortable.create(container, {
    ...store.state.drag_options,
    handle: '.drag-handle',
    onStart: () => {
      isDragging.value = true;
    },
    onEnd: ({ newIndex, oldIndex }) => {
      isDragging.value = false;
      const [moved] = fieldsModel.value.splice(oldIndex, 1);
      fieldsModel.value.splice(newIndex, 0, moved);
    },
  });
}
const isDragDropEnabled = computed(
  () => props.editMode && fieldsModel.value.length > 1,
);
watch(
  isDragDropEnabled,
  async (isEnabled) => {
    // Ensure the container is rendered before initializing sortable
    await nextTick();

    if (isEnabled) {
      initSortable();
      return;
    }

    if (sortable) {
      sortable.destroy();
      sortable = undefined;
    }
  },
  { immediate: true },
);

function addField() {
  Dialog.create({
    component: AddCustomFieldDialog,
    componentProps: {
      excludeKeys: ['separator']
    }
  }).onOk((customField) => {
    fieldsModel.value.push({
      _key: uid(),
      custom_field_key: customField._key,
      label: customField.default_label,
      hint: customField.default_hint,
      mandatory: false,
    });
  });
}

function deleteField(index) {
  fieldsModel.value.splice(index, 1);
}

function addSeparator() {
  fieldsModel.value.push({
    _key: uid(),
    custom_field_key: 'separator',
    label: null,
    hint: null,
    mandatory: false,
  });
}
</script>
