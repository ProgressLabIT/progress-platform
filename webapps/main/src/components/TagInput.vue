<template>
  <q-select
    v-model="model"
    :options="options"
    option-label="name"
    option-value="_key"
    multiple
    use-input
    use-chips
    :label="$capitalize($t('tag', 2))"
    filled
    @filter="onFilter"
    @new-value="onNewTag"
  />
</template>

<script setup>
import { ref } from 'vue';
import { api } from '@/boot/axios';
import multiMatch from '@/lib/MultiFieldSearch';

const model = defineModel();

const isLoading = ref(false);
const tags = ref([]);
(async () => {
  isLoading.value = true;
  const { data } = await api.get('/tag');
  tags.value = data.detail;
  isLoading.value = false;
})();
const options = ref(tags.value);

async function onNewTag(tagName, done) {
  if (tagName.length < 3 || tags.value.some(({ name }) => name === tagName)) {
    done();
    return;
  }

  isLoading.value = true;
  const {
    data: { detail },
  } = await api.post('/tag', { name: tagName });
  tags.value.push(detail);
  options.value.push(detail);
  isLoading.value = false;
  done(detail);
}

function onFilter(searchTerm, update) {
  if (searchTerm === '') {
    update(() => {
      options.value = tags.value;
    });
    return;
  }

  update(() => {
    options.value = tags.value.filter((tag) =>
      multiMatch(searchTerm, tag, ['name']),
    );
  });
}
</script>
