<template>
  <div class="fit q-pa-xl scroll">
    <div class="row item-center q-mb-xl">
      <div class="text-h2 display highlight">{{ title }}</div>

      <q-space />

      <template v-if="editMode">
        <q-btn
          type="submit"
          form="settings-form"
          size="12px"
          color="theme-blue"
          class="q-ml-auto"
          :label="$t('save')"
        />
        <q-btn
          size="12px"
          class="q-ml-md"
          color="theme-grey"
          :label="$t('cancel')"
          @click="cancel"
        />
      </template>
      <BaseTooltipIcon
        v-else
        icon="mdi-pencil"
        :tooltip="$capitalize($t('edit'))"
        :color="$theme.blue"
        @icon-click="editMode = true"
      />
    </div>

    <q-form id="settings-form" @submit="save">
      <slot v-bind="{ editMode }" />
    </q-form>
  </div>
</template>

<script setup>
import { Notify } from 'quasar';
import { ref } from 'vue';
import { useI18n } from 'vue-i18n';
import BaseTooltipIcon from '@/components/BaseTooltipIcon.vue';

const props = defineProps({
  title: {
    type: String,
    required: true,
  },
  // Using a function prop instead of event for full control over the save
  saveFn: {
    type: Function,
    required: true,
  },
});

const emit = defineEmits(['cancel']);

const editMode = ref(false);

const { t } = useI18n();
async function save() {
  try {
    await props.saveFn();
    editMode.value = false;
  } catch (error) {
    console.error(error);
    Notify.create({
      message: t('errors.save_err'),
      color: 'negative',
    });
  }
}

function cancel() {
  editMode.value = false;
  emit('cancel');
}
</script>
