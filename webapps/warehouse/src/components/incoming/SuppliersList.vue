<template>
  <div class="q-pa-md">
    <div class="text-subtitle1 q-py-xl text-center">
      {{ $t('incoming.suppliers.title') }}
    </div>
    <q-table
      flat
      bordered
      grid
      :title="$t('incoming.suppliers.suppliers')"
      :rows="rows"
      :columns="columns"
      row-key="_key"
      :filter="filter"
      :rows-per-page-options="[0]"
      hide-header
    >
      <template #top-right>
        <q-input
          v-model="filter"
          dense
          debounce="300"
          :placeholder="$t('incoming.suppliers.search')"
        >
          <template #append>
            <q-icon name="mdi-magnify" />
          </template>
        </q-input>
      </template>

      <template #item="{ row }">
        <div
          class="q-pa-xs col-xs-12 col-sm-6 col-md-4 col-lg-3 grid-style-transition"
        >
          <q-card
            v-ripple
            bordered
            flat
            class="my-box cursor-pointer q-hoverable"
            @click="$emit('supplierSelected', row)"
          >
            <q-card-section>
              <div>{{ row.name }}</div>
            </q-card-section>

            <q-separator />
            <q-list dense>
              <q-item v-for="document in row.documents" :key="document._key">
                <q-item-section>
                  <q-item-label>{{ document.name }}</q-item-label>
                </q-item-section>
                <q-item-section side>
                  <q-item-label caption
                    >{{ document.checked_rows }} /
                    {{ document.rows }}</q-item-label
                  >
                </q-item-section>
              </q-item>
            </q-list>
          </q-card>
        </div>
      </template>

      <template #no-data> {{ $t('incoming.suppliers.no_data') }}</template>
    </q-table>
  </div>
</template>

<script>
import { ref } from 'vue';

const columns = [
  {
    name: 'name',
    required: true,
    align: 'left',
    field: (row) => row.name,
    format: (val) => `${val}`,
    sortable: true,
  },
  {
    documents: 'documents',
    align: 'center',
    field: 'documents',
    sortable: false,
  },
];

const rows = [
  {
    name: 'Supplier 1',
    _key: 'SUP1',
    documents: [
      {
        name: 'DDT123',
        _key: 'DDT123',
        rows: '12',
        checked_rows: '9',
      },
      {
        name: 'DDT456',
        _key: 'DDT123',
        rows: '2',
        checked_rows: '2',
      },
    ],
  },

  {
    name: 'Supplier 2',
    _key: 'SUP2',
    documents: [
      {
        name: 'DDT123',
        _key: 'DDT123',
        rows: '12',
        checked_rows: '9',
      },
      {
        name: 'DDT456',
        _key: 'DDT123',
        rows: '2',
        checked_rows: '2',
      },
    ],
  },

  {
    name: 'Supplier 3',
    _key: 'SUP3',
    documents: [
      {
        name: 'DDT123',
        _key: 'DDT123',
        rows: '12',
        checked_rows: '9',
      },
      {
        name: 'DDT456',
        _key: 'DDT123',
        rows: '2',
        checked_rows: '2',
      },
    ],
  },

  {
    name: 'Supplier 4',
    _key: 'SUP4',
    documents: [
      {
        name: 'DDT123',
        _key: 'DDT123',
        rows: '12',
        checked_rows: '9',
      },
      {
        name: 'DDT456',
        _key: 'DDT123',
        rows: '2',
        checked_rows: '2',
      },
    ],
  },

  {
    name: 'Supplier 5',
    _key: 'SUP5',
    documents: [
      {
        name: 'DDT123',
        _key: 'DDT123',
        rows: '12',
        checked_rows: '9',
      },
      {
        name: 'DDT456',
        _key: 'DDT123',
        rows: '2',
        checked_rows: '2',
      },
    ],
  },

  {
    name: 'Sender 1',
    _key: 'SEN1',
    documents: [
      {
        name: 'DDT123',
        _key: 'DDT123',
        rows: '12',
        checked_rows: '9',
      },
      {
        name: 'DDT456',
        _key: 'DDT123',
        rows: '2',
        checked_rows: '2',
      },
    ],
  },

  {
    name: 'Sender 2',
    _key: 'SEN2',
    documents: [
      {
        name: 'DDT123',
        _key: 'DDT123',
        rows: '12',
        checked_rows: '9',
      },
      {
        name: 'DDT456',
        _key: 'DDT123',
        rows: '2',
        checked_rows: '2',
      },
    ],
  },

  {
    name: 'Sender 3',
    _key: 'SEN3',
    documents: [
      {
        name: 'DDT123',
        _key: 'DDT123',
        rows: '12',
        checked_rows: '9',
      },
      {
        name: 'DDT456',
        _key: 'DDT123',
        rows: '2',
        checked_rows: '2',
      },
    ],
  },

  {
    name: 'Sender 4',
    _key: 'SEN4',
    documents: [
      {
        name: 'DDT123',
        _key: 'DDT123',
        rows: '12',
        checked_rows: '9',
      },
      {
        name: 'DDT456',
        _key: 'DDT123',
        rows: '2',
        checked_rows: '2',
      },
    ],
  },
];

export default {
  name: 'SuppliersList',

  emits: ['supplierSelected'],

  setup() {
    return {
      filter: ref(''),
      columns,
      rows,
    };
  },
};
</script>

<style lang="sass">
.grid-style-transition
  transition: transform .28s, background-color .28s
</style>
