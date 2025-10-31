<template>
  <!-- TODO: Create a better base component for using with custom dialog plugin components -->
  <BaseDialog :show="true" :get-dialog-ref="getDialogRef" @close="onDialogHide">
    <q-card class="surface1 column" style="height: 90vh; min-width: 90vw">
      <q-card-section class="display text-h3 col-auto">
        {{ title }}
      </q-card-section>

      <q-separator />

      <q-card-section class="q-pt-sm row col">
        <!-- FILTERS COLUMN -->
        <div class="col-3 column q-pr-md q-gutter-y-sm">

          <!-- TEXT SEARCH -->
          <div class="text-h6 uppercase q-mb-sm">
            {{ $t('search_text') }}
          </div>
          <q-checkbox
            v-model="searchDescription"
            dense
            :label="$t('massCopyProcess.searchDescription')"
          />
          <q-input
            v-model="includeText"
            filled
            dense
            debounce="200"
            :label="$t('massCopyProcess.includesText')"
          />
          <q-input
            v-model="excludeText"
            filled
            dense
            debounce="200"
            :label="$t('massCopyProcess.excludesText')"
          />

          <q-separator class="q-my-md" />

          <!-- TAG SEARCH -->
          <div class="text-h6 uppercase q-mb-sm">
            {{ $t('search_tags') }}
          </div>
          <TagInput
            v-model="includeTags"
            dense
            :option-disable="
              ({ _key }) =>
                excludeTags.some(({ _key: key }) => key === _key)
            "
            :label="$t('massCopyProcess.includesTags')"
            clearable
          />
          <div class="col-auto">
            <q-btn-toggle
              v-model="includeTagsOperator"
              :options="[
                { label: $t('all', 2), value: 'ALL' },
                { label: $t('any'), value: 'ANY' },
              ]"
              size="sm"
            />
          </div>
          <TagInput
            v-model="excludeTags"
            dense
            :option-disable="
              ({ _key }) =>
                includeTags.some(({ _key: key }) => key === _key)
            "
            :label="$t('massCopyProcess.excludesTags')"
            clearable
          />
          <div class="col-auto">
            <q-btn-toggle
              v-model="excludeTagsOperator"
              :options="[
                { label: $t('all', 2), value: 'ALL' },
                { label: $t('any'), value: 'ANY' },
              ]"
              size="sm"
            />
          </div>

        </div>
        <!-- END OF FILTERS COLUMN -->

        <q-separator vertical />

        <!-- FILTERED ITEMS COLUMN -->
        <div class="col column full-height">
          <div class="row col-auto items-center q-my-sm q-px-md justify-between">
            <div class="text-h5 uppercase">
              {{ $t('countInfo.shown') }}: {{ filteredProducts?.length }}
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
                  :model-value="!!selectedProducts.find(i => i._key === item._key)"
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

        <q-separator vertical />

        <!-- SELECTED ITEMS COLUMN -->
        <div class="col column full-height">
          <div class="col-auto row items-center q-my-sm q-px-md justify-between">
            <div class="text-h5 uppercase">
              {{ $t('countInfo.selected', selectedProducts?.length) }}
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
            :items="selectedProducts.toSorted((a, b) => a.code > b.code ? 1 : -1)"
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
  baseFilters: {
    type: Object,
    default: () => ({
      hasOperationKey: null,
      excludeProductKey: null
    })
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

const searchDescription = ref(false);

const includeText = ref(props.defaultFilters?.includeText ?? '');
const excludeText = ref(props.defaultFilters?.excludeText ?? '');

const includeTags = ref(props.defaultFilters?.includeTags ?? []);
const excludeTags = ref(props.defaultFilters?.excludeTags ?? []);

const filteredProducts = ref([]);
const selectedProducts = ref([]);
const includeTagsOperator = ref('ALL');
const excludeTagsOperator = ref('ANY');

function toggleProduct(product) {
  const idx = selectedProducts.value.findIndex(p => p._key === product._key)
  if (idx !== - 1) {
    selectedProducts.value.splice(idx, 1)
  } else {
    selectedProducts.value.push(product);
  }
}

watch(
  [
    searchDescription,
    includeText,
    excludeText,
    includeTags,
    excludeTags,
    includeTagsOperator,
    excludeTagsOperator,
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
  const paramsObj = {
    search_description: searchDescription.value,
    include_tags_operator: includeTagsOperator.value,
    exclude_tags_operator: excludeTagsOperator.value,
    exclude_product_key: props.baseFilters.excludeProductKey,
    include_text: includeText.value.length > 0 ? includeText.value : null,
    exclude_text: excludeText.value.length > 0 ? excludeText.value : null,
    has_operation_key: props.baseFilters.hasOperationKey,
    details: false,
    active_only: true,
  };

  // Filter out null/undefined values to avoid sending them as strings
  const params = new URLSearchParams(
    Object.entries(paramsObj).filter(([_, v]) => v != null)
  );

  if (includeTags.value.length > 0) {
    includeTags.value.forEach(tag => {
      params.append('include_tags', tag._key);
    });
  }
  if (excludeTags.value.length > 0) {
    excludeTags.value.forEach(tag => {
      params.append('exclude_tags', tag._key);
    });
  }

  const { data } = await api.get('/product', { params });
  filteredProducts.value = data.filter(p => p._key !== props.baseFilters.excludeProductKey);
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
