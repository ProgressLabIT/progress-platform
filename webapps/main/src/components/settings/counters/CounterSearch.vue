<template>
  <q-card square class="surface1" style="min-width: 400px">
    <q-card-section>
      <q-input
        v-model="search_text"
        :label="$capitalize($t('search'))"
        icon="mdi-magnify"
        debounce="300"
        dense
        square
        filled
        class="full-width"
      >
        <template #append>
          <q-icon name="mdi-magnify" />
        </template>
      </q-input>
    </q-card-section>

    <q-card-section>
      <q-virtual-scroll
        v-slot="{ item }"
        style="max-height: 200px"
        :items="filtered_counters"
        class="surface2"
      >
        <q-item clickable @click="$emit('select', item)">
          <q-item-section>
            <q-item-label>
              <span class="highlight">
                {{ item.name }}
              </span>
            </q-item-label>
            <q-item-label v-if="item.template" caption>
              {{ template(item) }}
            </q-item-label>
          </q-item-section>
        </q-item>
      </q-virtual-scroll>
    </q-card-section>

    <q-card-section>
      <q-btn
        color="theme-blue"
        :label="$t('new')"
        icon="mdi-plus"
        class="full-width q-"
        @click="show_new_counter = true"
      >
      </q-btn>
    </q-card-section>

    <BaseDialog :show="show_new_counter" @close="show_new_counter = false">
      <CounterNew
        @close="
          () => {
            show_new_counter = false;
            fetchCounters();
          }
        "
      />
    </BaseDialog>
  </q-card>
</template>

<script>
import BaseDialog from '@/components/BaseDialog.vue';
import CounterNew from '@/components/settings/counters/CounterNew.vue';
import multiMatch from '@/lib/MultiFieldSearch.js';

export default {
  name: 'CounterSearch',

  components: {
    CounterNew,
    BaseDialog,
  },

  props: {
    excludeKeys: {
      type: Array,
      default: () => [],
    },
  },

  emits: ['select'],

  data() {
    return {
      search_text: null,
      counter_list: [],
      show_new_counter: false,
      search_counters: ['name'],
    };
  },

  computed: {
    filtered_counters() {
      return this.counter_list
        .filter((f) => !this.excludeKeys.includes(f._key))
        .filter((f) => multiMatch(this.search_text, f, this.search_counters));
    },
  },

  created() {
    this.fetchCounters();
  },

  methods: {
    fetchCounters() {
      this.$api.get('counter').then((resp) => {
        this.counter_list = resp.data;
      });
    },

    template(item) {
      if (item.template) {
        return item.template.join(' ');
      }
      return '';
    },
  },
};
</script>
