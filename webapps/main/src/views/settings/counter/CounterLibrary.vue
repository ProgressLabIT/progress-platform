<template>
  <LoadingSignal v-if="!data_ready" />

  <q-splitter v-else v-model="splitter_model" class="absolute-full">
    <template #before>
      <div class="full-height column">
        <q-input
          v-model="search_text"
          dense
          filled
          class="q-px-md q-pt-md"
          :placeholder="$capitalize($t('search'))"
        >
          <template #append>
            <q-icon name="mdi-magnify" />
          </template>
        </q-input>

        <div
          class="row q-mt-md q-px-lg q-py-sm text-h6 text-uppercase weight-bold"
        >
          <div class="col ellipsis">
            {{ $t('name') }}
          </div>
          <div class="col-3 ellipsis">
            {{ $t('next_tick') }}
          </div>
        </div>

        <q-separator />

        <q-scroll-area class="col">
          <div
            v-for="(counter, index) in filtered_counters"
            :key="counter._key"
            class="row pointer q-px-lg q-py-xs medium overflow-hidden"
            :class="{
              'alternate-row': index % 2 === 0,
              'bg-blue-backdrop': counter._key === selected_counter_key,
            }"
            @click="showCounterDetail(counter._key)"
          >
            <div class="col ellipsis">
              {{ $capitalize(counter.name) }}
            </div>
            <div class="col-3 ellipsis">
              {{ $capitalize(counter.next_tick) }}
            </div>
          </div>
        </q-scroll-area>

        <q-separator />

        <div class="row flex-center smaller q-py-xs">
          {{ filtered_counters.length }} {{ $t('of') }} {{ counter_list.length }}
        </div>

        <div class="q-pa-md q-mt-auto">
          <q-btn
            class="full-width q-mt-auto"
            color="theme-blue"
            :label="$t('new')"
            @click="show_new_counter_form = true"
          >
          </q-btn>
        </div>
      </div>
    </template>

    <template #after>
      <!-- COUNTER DATA -->
      <div class="col full-height">
        <router-view :counter="selected_counter" @reload="getCounters" />
      </div>
    </template>
  </q-splitter>

  <BaseDialog
    :show="show_new_counter_form"
    :no-backdrop-dismiss="false"
    @close="show_new_counter_form = false"
  >
    <CounterNew @close="show_new_counter_form = false" @created="getCounters">
    </CounterNew>
  </BaseDialog>
</template>

<script>
import BaseDialog from '@/components/BaseDialog.vue';
import LoadingSignal from '@/components/LoadingSignal.vue';
import CounterNew from '@/components/settings/counters/CounterNew.vue';
import multiMatch from '@/lib/MultiFieldSearch.js';

export default {
  name: 'CounterLibrary',

  components: {
    BaseDialog,
    CounterNew,
    LoadingSignal,
  },

  data() {
    return {
      data_ready: false,
      search_text: undefined,
      counter_list: [],
      show_new_counter_form: false,
      splitter_model: 30,
    };
  },

  computed: {
    selected_counter_key() {
      return this.$route.params.counter_key;
    },

    selected_counter() {
      return this.counter_list.find(
        (counter) => counter._key == this.selected_counter_key,
      );
    },

    filtered_counters() {
      const counters_to_search = ['name'];
      return this.counter_list.filter((counter) =>
        multiMatch(this.search_text, counter, counters_to_search),
      );
    },
  },

  created() {
    this.getCounters();
  },

  methods: {
    showCounterDetail(counter_key) {
      this.$router.push({
        name: 'counterDetail',
        params: { counter_key },
      });
    },
    getCounters() {
      this.$api.get('counter').then((resp) => {
        this.counter_list = resp.data.sort();
        this.data_ready = true;
      });
    },
  },
};
</script>
