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
            {{ $t('product.code') }}/{{ $t('description')}}
          </div>
          <q-input
            v-model="textToInclude"
            filled
            :label="$t('massCopyProcess.includesText')"
          />
          <q-input
            v-model="textToExclude"
            filled
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
                ({ _key }) => tagsToExclude.some(({ _key: key }) => key === _key)
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
                ({ _key }) => tagsToInclude.some(({ _key: key }) => key === _key)
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
        <!-- TODO: change design (?) -->
        <div class="col-6 column full-height">

          <div class="row col-auto items-center q-my-sm">
            <div class="text-h5 uppercase">
              {{ $t('countInfo.filtered', { count: filteredProducts.length, total: products.length }) }}
            </div>
            <q-btn
              size="xs"
              icon="mdi-checkbox-marked-outline"
              padding="xs sm"
              label="seleziona tutti"
              color="theme-grey"
              class="q-ml-md"
              @click="selectedProducts = [...filteredProducts]">
            </q-btn>
          </div>
          <q-list class="col scroll fit">
            <q-item
              v-for="p in filteredProducts"
              :key="p._key"
              clickable
              style="min-height: none"
              @click="toggleProduct(p)">
              <q-item-section side>
                <q-checkbox
                  size="sm"
                  dense
                  class="passive-checkbox"
                  :model-value="selectedProducts.includes(p)"
                  @click="toggleProduct(p)"
                />
              </q-item-section>
              <q-item-section>
                <q-item-label class="highlight">
                  {{ p.code }}
                </q-item-label>
                <q-item-label caption class="ellipsis">
                  {{ p.description }}
                </q-item-label>
              </q-item-section>
            </q-item>
          </q-list>
        </div>

        <div class="col column full-height">
          <div class="col-auto row items-center q-my-sm">
            <div class="text-h5 uppercase">
              {{ $t('countInfo.selected', selectedProducts.length) }}
            </div>
            <q-btn
              size="xs"
              padding="xs sm"
              icon="mdi-checkbox-blank-off-outline"
              label="deseleziona tutti"
              color="theme-grey"
              class="q-ml-md"
              @click="selectedProducts = []">
            </q-btn>
          </div>
          <q-list class="col scroll fit">
            <q-item
              v-for="p in selectedProducts.toSorted((a, b) => a.code - b.code)"
              :key="p._key"
              style="min-height: none">
              <q-item-section side>
                <q-btn
                  flat
                  round
                  icon="mdi-close"
                  size="sm"
                  @click="toggleProduct(p)"
                />
              </q-item-section>
              <q-item-section>
                <q-item-label class="highlight">
                  {{ p.code }}
                </q-item-label>
                <q-item-label caption class="ellipsis">
                  {{ p.description }}
                </q-item-label>
              </q-item-section>
            </q-item>
          </q-list>
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
import { computed, ref } from 'vue';
import BaseDialog from '@/components/BaseDialog.vue';
import multiMatch from '@/lib/MultiFieldSearch';
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

function toggleProduct(product_key) {
  if (selectedProducts.value.includes(product_key)) {
    selectedProducts.value.splice(selectedProducts.value.indexOf(product_key), 1)
  }
  else {
    selectedProducts.value.push(product_key)
  }
}

// const hiddenSelectedCount = computed(() => {
//   if (!tableRef.value) {
//     return 0;
//   }

//   const displayedRows = tableRef.value.computedRows;
//   return selectedProducts.value.filter(
//     ({ _key }) => !displayedRows.some((row) => row._key === _key),
//   ).length;
// });

/**
 * @type {NonNullable<import('quasar').QTableProps['filterMethod']>}
 */
const filteredProducts = computed(() => {
  if (
    tagsToInclude.value.length === 0 &&
    tagsToExclude.value.length === 0 &&
    !textToInclude.value &&
    !textToExclude.value
  ) {
    return props.products;
  }

  const condition = (isEmpty, value) =>
    globalOperator.value === 'AND' ? isEmpty || value : !isEmpty && value;
  const combineConditions = (...conditions) =>
    conditions[globalOperator.value === 'AND' ? 'every' : 'some'](
      (condition) => condition,
    );
  const includeTagsMethod =
    includeTagsOperator.value === 'AND' ? 'every' : 'some';
  const excludeTagsMethod =
    excludeTagsOperator.value === 'AND' ? 'every' : 'some';

  return props.products.filter((product) => {
    const tags = product.tags.map(({ _key }) => _key);

    return combineConditions(
      condition(
        textToInclude.value === '',
        multiMatch(textToInclude.value, product, ['code', 'description']),
      ),
      condition(
        textToExclude.value === '',
        !multiMatch(textToExclude.value, product, ['code', 'description']),
      ),
      condition(
        tagsToInclude.value.length === 0,
        tagsToInclude.value[includeTagsMethod](({ _key }) => tags.includes(_key)),
      ),
      condition(
        tagsToExclude.value.length === 0,
        tagsToExclude.value[excludeTagsMethod](({ _key }) => !tags.includes(_key)),
      ),
    );
  });
});

const globalOperator = ref('AND');
const includeTagsOperator = ref('AND');
const excludeTagsOperator = ref('AND');
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
