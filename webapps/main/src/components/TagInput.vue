<template>
  <q-select
    ref="selectRef"
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
  >
    <template #no-option="{ inputValue }">
      <q-item v-if="inputValue.length < MIN_CHARS">
        <q-item-section class="text-low">
          {{ $t('tagInput.noData', { minChars: MIN_CHARS }) }}
        </q-item-section>
      </q-item>
      <q-item v-else clickable @click="createAndAddNewTag(inputValue)">
        <q-item-section avatar>
          <q-icon name="mdi-plus" />
        </q-item-section>

        <q-item-section>
          <q-item-label>
            {{ $t('tagInput.create.label', { name: inputValue }) }}
          </q-item-label>

          <q-item-label caption>
            <i18n-t keypath="tagInput.create.hint">
              <template #key>
                <kbd>Enter</kbd>
              </template>
            </i18n-t>
          </q-item-label>
        </q-item-section>
      </q-item>
    </template>
  </q-select>
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

const MIN_CHARS = 3;

async function onNewTag(tagName, done) {
  if (
    tagName.length < MIN_CHARS ||
    tags.value.some(({ name }) => name === tagName)
  ) {
    done();
    return;
  }

  const newTag = await createNewTag(tagName);
  done(newTag);
}
/** @type {import('vue'.Ref<import('quasar').QSelect>} */
const selectRef = ref();
async function createAndAddNewTag(tagName) {
  const newTag = await createNewTag(tagName);
  model.value.push(newTag);
  selectRef.value.updateInputValue('');
  selectRef.value.focus();
}

async function createNewTag(tagName) {
  isLoading.value = true;
  const {
    data: { detail },
  } = await api.post('/tag', { name: tagName });
  tags.value.push(detail);
  options.value.push(detail);
  isLoading.value = false;
  return detail;
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
