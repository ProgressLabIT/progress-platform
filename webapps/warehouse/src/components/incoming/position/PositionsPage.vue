<template>
  <q-scroll-area :visible="false" style="height: 50vh">
    <q-table
      v-model:selected="selected"
      flat
      bordered
      grid
      :loading="loading"
      :title="$t('incoming.positions.positions')"
      :rows="rows"
      :columns="columns"
      row-key="_key"
      :rows-per-page-options="[0]"
      hide-header
      selection="multiple"
    >
      <template #top-right>
        <q-input
          v-model="filter"
          dense
          debounce="300"
          :placeholder="$t('incoming.positions.search')"
        >
          <template #append>
            <q-icon name="mdi-magnify" />
          </template>
        </q-input>
      </template>

      <template #item="props">
        <div
          class="q-pa-xs col-xs-12 col-sm-6 col-md-4 col-lg-3 grid-style-transition"
          :style="props.selected ? 'transform: scale(0.95);' : ''"
        >
          <!-- <q-card
            v-ripple
            bordered
            flat
            class="my-box cursor-pointer q-hoverable"
            @click="$emit('positionSelected', row)"
          > -->
          <q-card
            v-ripple
            bordered
            flat
            class="my-box cursor-pointer q-hoverable"
            @click="toggleSelection(props.row)"
          >
            <!--q-card-section>
              <div>{{ row.code }}</div>
            </q-card-section> -->
            <q-card-section>
              <q-checkbox
                v-model="props.selected"
                dense
                :label="props.row.code"
              />
            </q-card-section>
            <q-separator />
            <q-list dense>
              <q-item :key="`desc ${props.row._key}`">
                <q-item-section>
                  <q-item-label>{{ props.row.description }}</q-item-label>
                </q-item-section>
              </q-item>
            </q-list>
          </q-card>
        </div>
      </template>

      <template #no-data> {{ $t('incoming.positions.no_data') }}</template>
    </q-table>
  </q-scroll-area>
  <div style="height: 30vh">
    <div class="fit row justify-center items-start content-center">
      <q-btn
        color="theme-blue"
        :label="$t('incoming.positions.create_container')"
        class="col-12"
        @click="
          (event) => {
            event.stopPropagation();
            showCreateContainerBottomSheet();
          }
        "
      ></q-btn>
      <q-btn
        color="theme-blue"
        :label="$t('back')"
        class="col-6"
        @click="$emit('back')"
      ></q-btn>
      <q-btn
        color="theme-blue"
        :label="$t('next')"
        class="col-6"
        @click="selectPosition()"
      ></q-btn>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue';

const columns = [
  {
    name: 'code',
    required: true,
    align: 'left',
    field: (row) => row.name,
    format: (val) => `${val}`,
    sortable: true,
  },
  {
    name: 'description',
    required: true,
    align: 'left',
    field: (row) => row.serial,
    format: (val) => `${val}`,
    sortable: false,
  },
];

const rows = [
  {
    code: 'position 1',
    _key: 'POS 1',
    description: 'xxxxxx',
  },
  {
    code: 'position 2',
    _key: 'POS 2',
    description: 'xxxxxx',
  },
  {
    code: 'position 3',
    _key: 'POS 3',
    description: 'xxxxxx',
  },
  {
    code: 'position 4',
    _key: 'POS 4',
    description: 'xxxxxx',
  },
  {
    code: 'position 5',
    _key: 'POS 5',
    description: 'xxxxxx',
  },
  {
    code: 'position 6',
    _key: 'POS 6',
    description: 'xxxxxx',
  },
];

export default {
  name: 'PositionsPage',

  props: {
    product: {
      type: Object,
      required: true,
    },
    supplier: {
      type: Object,
      required: true,
    },
    quantity: {
      type: Number,
      required: true,
    },
  },

  emits: ['positionSelected', 'back'],

  setup() {
    return {
      filter: ref(''),
      selected: ref([]),
      columns,
      rows,
    };
  },

  data() {
    return {
      show_code_scanner: false,
      loading: false,
      last_research: undefined,
    };
  },

  watch: {
    filter: {
      handler() {
        if (this.filter !== this.last_research) {
          this.loadPositions(this.filter);
        }
      },
    },
  },

  created() {
    this.$bus.on('containers-created', (containers) => {
      this.$emit('positionSelected', containers);
    });
  },

  methods: {
    loadPositions(filter) {
      this.loading = true;
      let params = {};

      if (filter) {
        params.search = filter;
        this.last_research = filter;
      }
      params.limit = 100;

      this.$api
        .get('position', {
          params,
        })
        .then((resp) => {
          this.rows = this.selected.concat(resp.data);
          this.loading = false;
        });
      this.loading = false;
    },
    showCreateContainerBottomSheet() {
      this.$bus.emit('show-create-container');
    },
    toggleSelection(row) {
      const index = this.selected.findIndex((el) => el._key === row._key);
      if (index >= 0) {
        this.selected.splice(index, 1);
      } else {
        this.selected.push(row);
      }
    },
    selectPosition() {
      if (this.selected.length > 0) {
        this.$emit('positionSelected', this.selected);
      }
    },
  },
};
</script>

<style lang="sass">
.grid-style-transition
  transition: transform .28s, background-color .28s
</style>
