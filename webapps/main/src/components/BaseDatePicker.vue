<template>
  <q-input
    v-model="date"
    filled
    :dense="dense"
    clearable
    debounce="1000"
    mask="####-##-##"
    :rules="[(v) => !v || isValidISODate(v) || $t('invalid_date')]"
    hide-bottom-space
    :label="label"
  >
    <template #append>
      <q-icon name="mdi-calendar" size="xs" class="cursor-pointer">
        <q-popup-proxy
          cover
          transition-show="scale"
          transition-hide="scale"
        >
          <q-date v-model="date" mask="YYYY-MM-DD" minimal>
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

// Model is ISO (YYYY-MM-DD) — what the backend's Pydantic `date` fields
// expect. The input mask and q-date mask both use dashes so the bound
// value is ISO directly, no conversion needed.
const date = defineModel({
  type: String,
  required: true,
});

// The mask only enforces digit positions, not ranges. Reject impossible
// dates (month 77, Feb 30, …) by round-tripping through a local Date: if the
// constructed parts don't match the input, the value overflowed.
function isValidISODate(v) {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(v);
  if (!m) return false;
  const [, y, mo, d] = m.map(Number);
  const dt = new Date(y, mo - 1, d);
  return dt.getFullYear() === y && dt.getMonth() === mo - 1 && dt.getDate() === d;
}
</script>
