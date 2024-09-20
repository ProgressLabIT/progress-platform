<template>
  <!-- TODO: Create a better base component for using with custom dialog plugin components -->
  <BaseDialog :show="true" :get-dialog-ref="getDialogRef" @close="onDialogHide">
    <q-card class="surface1 column" style="height: 90vh; min-width: 1100px">
      <q-card-section class="display text-h3 col-auto">
        {{ title }}
      </q-card-section>

      <q-separator />

      <q-card-section class="items-center col-auto q-mb-sm">
        <span>{{ $t('massCopyProcess.conditions') }}</span>

        <q-btn-toggle
          v-model="globalOperator"
          :options="[
            { label: $t('all', 2), value: 'AND' },
            { label: $t('any'), value: 'OR' },
          ]"
          size="sm"
          class="q-ml-md"
        />
      </q-card-section>

      <q-card-section class="q-col-gutter-md row col-auto q-pt-none">
        <div class="col-5 q-gutter-sm">
          <div class="text-h5 uppercase">
            {{ $t('product.code') }}/{{ $t('description') }}
          </div>
          <q-input
            v-model="textToInclude"
            filled
            debounce="200"
            :label="$t('massCopyProcess.includesText')"
          />
          <q-input
            v-model="textToExclude"
            filled
            debounce="200"
            :label="$t('massCopyProcess.excludesText')"
          />
        </div>

        <div class="col-auto">
          <q-separator vertical />
        </div>

        <div class="col q-gutter-sm">
          <div class="text-h5 uppercase">
            {{ $t('tag', 2) }}
          </div>
          <div class="row items-center">
            <TagInput
              v-model="tagsToInclude"
              :option-disable="
                ({ _key }) =>
                  tagsToExclude.some(({ _key: key }) => key === _key)
              "
              :label="$t('massCopyProcess.includesTags')"
              class="col"
              clearable
            />

            <div>
              <q-btn-toggle
                v-model="includeTagsOperator"
                :options="[
                  { label: $t('all', 2), value: 'AND' },
                  { label: $t('any'), value: 'OR' },
                ]"
                size="sm"
                class="q-ml-md"
              />
            </div>
          </div>
          <div class="row items-center">
            <TagInput
              v-model="tagsToExclude"
              :option-disable="
                ({ _key }) =>
                  tagsToInclude.some(({ _key: key }) => key === _key)
              "
              :label="$t('massCopyProcess.excludesTags')"
              class="col"
              clearable
            />

            <div>
              <q-btn-toggle
                v-model="excludeTagsOperator"
                :options="[
                  { label: $t('all', 2), value: 'AND' },
                  { label: $t('any'), value: 'OR' },
                ]"
                size="sm"
                class="q-ml-md"
              />
            </div>
          </div>
        </div>
      </q-card-section>

      <q-separator inset />

      <q-card-section class="q-pt-sm row col q-col-gutter-md">
        <!-- FILTERED ITEMS -->
        <div class="col-6 column full-height">
          <div class="row col-auto items-center q-my-sm">
            <div class="text-h5 uppercase">
              {{
                $t('countInfo.filtered', {
                  count: filteredProducts.length,
                  total: products.length,
                })
              }}
            </div>
            <q-btn
              size="xs"
              icon="mdi-checkbox-marked-outline"
              padding="xs sm"
              :label="$t('select_all')"
              color="theme-grey"
              class="q-ml-md"
              @click="selectedProducts = [...filteredProducts]"
            >
            </q-btn>
          </div>

          <q-virtual-scroll
            v-slot="{ item }"
            style="max-height: 100%"
            class="col fit"
            :items="filteredProducts"
          >
            <q-item
              key="_key"
              clickable
              style="min-height: none"
              @click="toggleProduct(item)"
            >
              <q-item-section side>
                <q-checkbox
                  size="sm"
                  dense
                  class="passive-checkbox"
                  :model-value="selectedProducts.includes(item)"
                  @click="toggleProduct(item)"
                />
              </q-item-section>
              <q-item-section>
                <q-item-label class="highlight">
                  {{ item.code }}
                </q-item-label>
                <q-item-label caption class="ellipsis">
                  {{ item.description }}
                </q-item-label>
              </q-item-section>
            </q-item>
          </q-virtual-scroll>
        </div>

        <!-- SELECTED ITEMS -->

        <div class="col column full-height">
          <div class="col-auto row items-center q-my-sm">
            <div class="text-h5 uppercase">
              {{ $t('countInfo.selected', selectedProducts.length) }}
            </div>
            <q-btn
              size="xs"
              padding="xs sm"
              icon="mdi-checkbox-blank-off-outline"
              :label="$t('deselect_all')"
              color="theme-grey"
              class="q-ml-md"
              @click="selectedProducts = []"
            >
            </q-btn>
          </div>
          <q-virtual-scroll
            v-slot="{ item }"
            class="col fit"
            style="max-height: 100%"
            :items="selectedProducts.toSorted((a, b) => a.code - b.code)"
          >
            <q-item key="_key" style="min-height: none">
              <q-item-section side>
                <q-btn
                  flat
                  round
                  icon="mdi-close"
                  size="sm"
                  @click="toggleProduct(item)"
                />
              </q-item-section>
              <q-item-section>
                <q-item-label class="highlight">
                  {{ item.code }}
                </q-item-label>
                <q-item-label caption class="ellipsis">
                  {{ item.description }}
                </q-item-label>
              </q-item-section>
            </q-item>
          </q-virtual-scroll>
        </div>
      </q-card-section>

      <q-separator />

      <q-card-actions align="right">
        <q-btn
          :label="$t('cancel')"
          color="theme-grey"
          @click="onDialogCancel"
        />
        <q-btn
          :label="$t('copy')"
          color="primary"
          @click="onDialogOK(selectedProducts)"
        />
      </q-card-actions>
    </q-card>
  </BaseDialog>
</template>

<script setup>
import { useDialogPluginComponent } from 'quasar';
import { ref, watch } from 'vue';
import { api } from '@/boot/axios';
import BaseDialog from '@/components/BaseDialog.vue';
import TagInput from './TagInput.vue';

const props = defineProps({
  title: {
    type: String,
    required: true,
  },
  products: {
    type: Array,
    required: true,
  },
  defaultFilters: {
    type: Object,
    default: undefined,
  },
});

defineEmits(useDialogPluginComponent.emitsObject);

const { dialogRef, onDialogHide, onDialogOK, onDialogCancel } =
  useDialogPluginComponent();
// This can't be inside the template due to unwrapping
// See: https://github.com/vuejs/composition-api/issues/317#issuecomment-1069145915
const getDialogRef = () => dialogRef;

/** @type {import('vue').Ref<import('quasar').QTable>} */
// const tableRef = ref();

const textToInclude = ref(props.defaultFilters?.textToInclude ?? '');
const textToExclude = ref(props.defaultFilters?.textToExclude ?? '');

const tagsToInclude = ref(props.defaultFilters?.tagsToInclude ?? []);
const tagsToExclude = ref(props.defaultFilters?.tagsToExclude ?? []);

const selectedProducts = ref([]);
const filteredProducts = ref([]);

const globalOperator = ref('AND');
const includeTagsOperator = ref('AND');
const excludeTagsOperator = ref('AND');

function toggleProduct(product_key) {
  if (selectedProducts.value.includes(product_key)) {
    selectedProducts.value.splice(
      selectedProducts.value.indexOf(product_key),
      1,
    );
  } else {
    selectedProducts.value.push(product_key);
  }
}

watch(
  [
    textToInclude,
    textToExclude,
    tagsToInclude,
    tagsToExclude,
    includeTagsOperator,
    excludeTagsOperator,
    globalOperator,
  ],
  () => {
    filterProducts();
  },
  { deep: true },
);
/**
 * @type {NonNullable<import('quasar').QTableProps['filterMethod']>}
 */

async function filterProducts() {
  if (
    tagsToInclude.value.length === 0 &&
    tagsToExclude.value.length === 0 &&
    !textToInclude.value &&
    !textToExclude.value
  ) {
    filteredProducts.value = props.products;
  }

  let tags_to_include = '';
  let tags_to_exclude = '';
  for (const tag of tagsToInclude.value) {
    tags_to_include += tag._key + ' ';
  }
  for (const tag of tagsToExclude.value) {
    tags_to_exclude += tag._key + ' ';
  }
  const { data } = await api.get('/product/search', {
    params: {
      text_to_include: textToInclude.value,
      text_to_exclude: textToExclude.value,
      tags_to_include: tags_to_include,
      tags_to_exclude: tags_to_exclude,
      global_operator: globalOperator.value,
      include_tags_operator: includeTagsOperator.value,
      exclude_tags_operator: excludeTagsOperator.value,
    },
  });
  filteredProducts.value = data;
}

filterProducts();
</script>

<style scoped lang="scss">
.dialog-card {
  flex-flow: column;
  width: 100%;
  min-width: 400px;
  max-width: 1000px;
}
.q-checkbox.passive-checkbox:deep(.q-checkbox__inner):before {
  display: none;
}
</style>
