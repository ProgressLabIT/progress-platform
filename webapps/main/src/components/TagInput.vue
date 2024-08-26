<template>
  <q-select
    ref="selectRef"
    :model-value="model"
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
    @update:model-value="
      // clearable emits null
      model = $event === null ? [] : $event
    "
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

    <template #selected-item="scope">
      <q-chip
        dense
        removable
        color="theme-grey"
        :tabindex="scope.tabindex"
        @remove="scope.removeAtIndex(scope.index)"
      >
        {{ scope.opt.name }}
      </q-chip>
    </template>

    <template #after-options>
      <q-item v-if="search_text.length < MIN_CHARS">
        <q-item-section class="text-low">
          {{ $t('tagInput.after_options', { minChars: MIN_CHARS }) }}
        </q-item-section>
      </q-item>
      <q-item
        v-else-if="!exact_match"
        clickable
        @click="createAndAddNewTag(search_text)"
      >
        <q-item-section avatar>
          <q-icon name="mdi-plus" />
        </q-item-section>

        <q-item-section>
          <q-item-label>
            {{ $t('tagInput.create.label', { name: search_text }) }}
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

const model = defineModel({ type: Array });

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

let search_text = '';
let exact_match = false;
function onFilter(searchTerm, update) {
  search_text = searchTerm;
  exact_match = false;
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

  options.value.forEach((val) => {
    exact_match |= searchTerm.toUpperCase() === val['name'].toUpperCase();
  });
}
</script>
