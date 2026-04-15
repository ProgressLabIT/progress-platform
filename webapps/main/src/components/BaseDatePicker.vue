<template>
  <q-input
    v-model="date"
    filled
    :dense="dense"
    clearable
    debounce="1000"
    mask="date"
    :label="label"
  >
    <template #append>
      <q-icon name="mdi-calendar" size="xs" class="cursor-pointer">
        <q-popup-proxy
          cover
          transition-show="scale"
          transition-hide="scale"
        >
          <q-date v-model="date" minimal>
            <div class="row items-center justify-end">
              <q-btn v-close-popup label="Close" color="primary" flat />
            </div>
          </q-date>
        </q-popup-proxy>
      </q-icon>
    </template>
  </q-input>
</template>

<script setup>
defineProps({
  label: {
    type: String,
    required: true,
  },
  dense: {
    type: Boolean,
    default: false,
  },
});

const date = defineModel({
  type: String,
  required: true,
});
</script>
