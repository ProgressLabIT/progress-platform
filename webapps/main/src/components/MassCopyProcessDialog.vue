<template>
  <!-- TODO: Create a better base component for using with custom dialog plugin components -->
  <BaseDialog :show="true" :get-dialog-ref="getDialogRef" @close="onDialogHide">
    <q-card class="surface1 column dialog-card">
      <q-card-section class="display text-h3">
        {{
          $t(`massCopyProcess.title.${sourceProduct ? 'product' : 'operation'}`)
        }}
      </q-card-section>

      <q-separator />

      <q-card-section class="q-pl-lg q-pb-none flex items-center">
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

      <q-card-section class="q-gutter-sm">
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
      </q-card-section>

      <q-separator inset />

      <q-card-section class="col scroll q-pt-sm">
        <!-- TODO: change design (?) -->
        <q-table
          ref="tableRef"
          v-model:selected="selectedProducts"
          :rows="products"
          row-key="_key"
          selection="multiple"
          grid
          hide-bottom
          :filter="{
            tagsToInclude,
            tagsToExclude,
            textToInclude,
            textToExclude,
          }"
          :filter-method="filterProducts"
          :rows-per-page-options="[0]"
        >
          <template #top>
            <!-- TODO: Select/Unselect all/filtered -->
            {{
              $t('massCopyProcess.countInfo.filtered', {
                count: tableRef?.computedRowsNumber,
                total: products.length,
              })
            }}
            -
            {{
              $t('massCopyProcess.countInfo.selected', {
                count: selectedProducts.length,
              })
            }}
            <template v-if="hiddenSelectedCount > 0">
              ({{
                $t('massCopyProcess.countInfo.selectedHidden', {
                  count: hiddenSelectedCount,
                })
              }})
            </template>
          </template>

          <template #item="scope">
            <div
              class="col-6 col-sm-4 col-md-3 q-pa-xs q-table__grid-item"
              :class="{ 'q-table__grid-item--selected': scope.selected }"
            >
              <q-card class="fit">
                <q-card-section>
                  <q-checkbox v-model="scope.selected" dense>
                    <div class="text-h3 display ellipsis-2-lines">
                      {{ scope.row.code }}
                    </div>
                  </q-checkbox>

                  <div
                    class="q-mt-sm text-uppercase low-text px-0 pb-1 ellipsis-3-lines"
                  >
                    {{ scope.row.description }}
                  </div>
                </q-card-section>
              </q-card>
            </div>
          </template>
        </q-table>
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
import { useStore } from 'vuex';
import BaseDialog from '@/components/BaseDialog.vue';
import multiMatch from '@/lib/MultiFieldSearch';
import TagInput from './TagInput.vue';

const props = defineProps({
  sourceProduct: {
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
const tableRef = ref();

const store = useStore();

const textToInclude = ref('');
const textToExclude = ref('');

const tagsToInclude = ref(props.sourceProduct?.tags ?? []);
const tagsToExclude = ref([]);
const allProducts = computed(() => store.getters.productCatalog(true));
const products = computed(() =>
  props.sourceProduct
    ? allProducts.value.filter(({ _key }) => _key !== props.sourceProduct._key)
    : // TODO: Only show products that have phases that use the operation
      allProducts.value,
);
const selectedProducts = ref([]);

const hiddenSelectedCount = computed(() => {
  if (!tableRef.value) {
    return 0;
  }

  const displayedRows = tableRef.value.computedRows;
  return selectedProducts.value.filter(
    ({ _key }) => !displayedRows.some((row) => row._key === _key),
  ).length;
});

/**
 * @type {NonNullable<import('quasar').QTableProps['filterMethod']>}
 */
const filterProducts = (
  products,
  { tagsToInclude, tagsToExclude, textToInclude, textToExclude },
) => {
  if (
    tagsToInclude.length === 0 &&
    tagsToExclude.length === 0 &&
    !textToInclude &&
    !textToExclude
  ) {
    return products;
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

  return products.filter((product) => {
    const tags = product.tags.map(({ _key }) => _key);

    return combineConditions(
      condition(
        textToInclude === '',
        multiMatch(textToInclude, product, ['code', 'description']),
      ),
      condition(
        textToExclude === '',
        !multiMatch(textToExclude, product, ['code', 'description']),
      ),
      condition(
        tagsToInclude.length === 0,
        tagsToInclude[includeTagsMethod](({ _key }) => tags.includes(_key)),
      ),
      condition(
        tagsToExclude.length === 0,
        tagsToExclude[excludeTagsMethod](({ _key }) => !tags.includes(_key)),
      ),
    );
  });
};

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
</style>
