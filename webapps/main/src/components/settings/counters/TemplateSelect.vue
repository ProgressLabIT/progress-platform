<template>
  <q-select
    :model-value="model"
    filled
    :label="$t('template')"
    use-input
    use-chips
    multiple
    input-debounce="0"
    :options="filterOptions"
    class="q-mt-md"
    @new-value="createValue"
    @filter="filterFn"
  />
</template>

<script setup>
import { ref } from 'vue';

const templateOptions = ['%y', '%m', '%d', '/', '#2', '#3', '#4', '#5', '#6'];

const model = ref([]);
const filterOptions = ref(templateOptions);

function createValue(val, done) {
  if (val.length > 0) {
    const modelValue = (model.value || []).slice();

    val
      .split(/[,;|]+/)
      .map((v) => v.trim())
      .filter((v) => v.length > 0)
      .forEach((v) => {
        if (templateOptions.includes(v) === false) {
          templateOptions.push(v);
        }
        if (modelValue.includes(v) === false) {
          modelValue.push(v);
        }
      });

    model.value = modelValue;
    done(val);
  }
}

function filterFn(val, update) {
  update(() => {
    if (val === '') {
      filterOptions.value = templateOptions;
    } else {
      filterOptions.value = templateOptions.filter((v) => v.indexOf(val) > -1);
    }
  });
}
</script>
