<template>
  <q-table
    id="product_table"
    :columns="columns"
    :rows="products"
    row-key="_key"
    virtual-scroll
    hide-bottom
    dense
    class="full-height"
    separator="none"
    table-class="text-high"
    card-class="background no-shadow"
    :rows-per-page-options="[0]"
  >
    <template #body="props">
      <q-tr
        :key="props.row._key"
        :props="props"
        @dblclick="goToProductPage('productHome', props.row)"
      >
        <q-td key="code" :props="props" class="ellipsis">
          {{ props.row.code }}
        </q-td>

        <q-td key="description" :props="props" class="ellipsis">
          {{ props.row.description }}
          <q-tooltip
            v-if="props.row.description"
            :delay="500"
            anchor="top left"
            self="bottom left"
            :offset="[8, 6]"
            transition-show="fade"
            transition-hide="fade"
          >
            {{ props.row.description }}
          </q-tooltip>
        </q-td>

        <q-td key="tags" :props="props" class="ellipsis">
          <q-badge
            v-for="tag in props.row.tags"
            :key="tag._key"
            color="theme-grey"
            class="q-mr-xs"
          >
            {{ tag.name }}
          </q-badge>
        </q-td>

        <q-td key="active" :props="props">
          <q-toggle
            :toggle-indeterminate="false"
            :model-value="props.row.active"
            size="xs"
            dense
            @update:model-value="switchActiveState(props.row)"
          >
            <q-tooltip
              :delay="Number(100)"
              anchor="top middle"
              self="bottom middle"
              transition-show="scale"
              transition-hide="scale"
              transition-duration="200"
              class="text-body2 bg-theme-blue"
            >
              {{
                $capitalize(
                  props.row.active ? t('deactivate') : t('reactivate'),
                )
              }}
            </q-tooltip>
          </q-toggle>
        </q-td>

        <q-td key="actions" :props="props">
          <BaseTooltipIcon
            icon="mdi-clipboard-text"
            icon_size="xs"
            :tooltip="$capitalize(t('product.actions.details'))"
            :color="$theme.blue"
            @icon-click="goToProductPage('productHome', props.row)"
          />
          <BaseTooltipIcon
            icon="mdi-chevron-triple-right"
            icon_size="xs"
            :tooltip="$capitalize(t('process'))"
            :color="$theme.blue"
            @icon-click="goToProductPage('productionProcess', props.row)"
          />
          <BaseTooltipIcon
            icon="mdi-clipboard-list"
            icon_size="xs"
            :tooltip="$capitalize(t('component', 2))"
            :color="$theme.blue"
            @icon-click="goToProductPage('bom', props.row)"
          />
          <BaseTooltipIcon
            icon="mdi-content-copy"
            icon_size="xs"
            :tooltip="$capitalize(t('copy'))"
            :color="$theme.orange"
            @icon-click="showCopy(props.row)"
          />
          <BaseTooltipIcon
            icon="mdi-delete"
            icon_size="xs"
            :tooltip="$capitalize(t('delete'))"
            :color="$theme.red"
            @icon-click="confirmDelete(props.row)"
          />
        </q-td>
      </q-tr>
    </template>

    <template #bottom-row>
      <q-tr v-if="canLoadMore || loading || products.length === 0">
        <q-td colspan="100%" class="text-center">
          <q-btn
            v-if="canLoadMore"
            flat
            dense
            color="theme-blue"
            :label="t('load_more')"
            @click="emit('loadMore')"
          />
          <q-spinner v-if="loading" class="q-ml-sm" />
          <span
            v-if="!loading && products.length === 0"
            class="low-text"
          >
            {{ t('product.none_found') }}
          </span>
        </q-td>
      </q-tr>
    </template>
  </q-table>
</template>

<script setup>
import { useQuasar } from 'quasar';
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRoute, useRouter } from 'vue-router';
import { useStore } from 'vuex';
import { api } from '@/boot/axios.js';
import BaseTooltipIcon from '@/components/BaseTooltipIcon.vue';

defineProps({
  products: {
    type: Array,
    required: true,
  },
  canLoadMore: {
    type: Boolean,
    default: false,
  },
  loading: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(['loadMore']);

const $q = useQuasar();
const route = useRoute();
const router = useRouter();
const store = useStore();
const { t } = useI18n();

// table-layout: fixed (see sass below) — th widths drive the column proportions,
// overflowing cell text is truncated via the ellipsis class
const columns = computed(() => [
  {
    field: 'code',
    name: 'code',
    sortable: true,
    label: t('product.list_headers.code').toUpperCase(),
    align: 'left',
    headerStyle: 'width: 15%',
  },
  {
    field: 'description',
    name: 'description',
    sortable: true,
    label: t('product.list_headers.description').toUpperCase(),
    align: 'left',
    headerStyle: 'width: 40%',
  },
  {
    field: 'tags',
    name: 'tags',
    sortable: false,
    label: t('product.list_headers.tags').toUpperCase(),
    align: 'left',
    headerStyle: 'width: 20%',
  },
  {
    field: 'active',
    name: 'active',
    sortable: true,
    label: t('product.list_headers.active').toUpperCase(),
    align: 'center',
    headerStyle: 'width: 9%',
  },
  {
    field: 'actions',
    name: 'actions',
    sortable: false,
    label: t('product.list_headers.actions').toUpperCase(),
    align: 'right',
    headerStyle: 'width: 16%',
  },
]);

function switchActiveState(row) {
  store.dispatch('switchActiveState', row);
}

function goToProductPage(page, row) {
  router.push({
    name: page,
    params: {
      product_key: row._key,
    },
    query: {
      back_to: 'productList',
      ...route.query,
    },
  });
}

function showCopy(row) {
  $q.dialog({
    title: t('code') + ' ' + t('new') + ' ' + t('product.label'),
    prompt: {
      model: '',
      type: 'text',
      isValid: (val) => val.length > 0,
      cancel: true,
      persistent: true,
    },
  }).onOk((new_code) => {
    const data = {
      original_product: row._key,
      new_code,
    };
    api
      .post('product/copy', data)
      .then(async (resp) => {
        // Load product list to include navigation state for new product
        await store.dispatch('loadProductList', { limit: 100 });
        router.push({
          name: 'productHome',
          params: { product_key: resp.data.detail.new_product_key },
          query: { back_to: 'productList' },
        });
      })
      .catch((err) => {
        if (err.response.status === 400) {
          window.alert(err.response.data.detail.message);
        } else {
          $q.notify({
            message: err.response.data.detail,
            color: 'theme-red',
            position: 'top',
            icon: 'mdi-alert-circle',
            timeout: 3000,
          });
        }
      });
  });
}

function confirmDelete(row) {
  $q.dialog({
    title: row.code,
    message: t('product.confirm_delete_question'),
    cancel: true,
  }).onOk(() => {
    store.dispatch('moveToTrash', row);
    $q.notify({
      progress: true,
      message: t('product.snackbars.delete_confirmed', {
        code: row.code,
      }).toUpperCase(),
      color: 'theme-background',
      multiline: true,
      actions: [
        {
          label: t('confirm'),
          color: 'theme-blue',
        },
        {
          label: t('undo'),
          color: 'theme-orange',
          handler: () => store.dispatch('restoreProduct', row._key),
        },
      ],
    });
  });
}
</script>

<style lang="sass">
#product_table
  & table
    table-layout: fixed
    width: 100%
  & th
    font-weight: bold
    color: var(--text-low)
    border-bottom: 1px solid #fff2
  & td
    font-size: 14px

  .q-table__top,
  .q-table__bottom,
  thead tr:first-child th /* bg color is important for th; just specify one */
    background-color: var(--bg-color)

  thead tr th
    position: sticky
    z-index: 1
  /* this will be the loading indicator */
  thead tr:last-child th
    /* height of all previous header rows */
    top: 48px
  thead tr:first-child th
    top: 0
</style>
