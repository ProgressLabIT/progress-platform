<template>
  <LoadingSignal v-if="!data_ready" />

  <div v-else class="row full-height">
    <div class="full-height column col-3">
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
        <div class="col">
          {{ $t('name') }}
        </div>
        <div class="col-3">
          {{ $t('next_tick') }}
        </div>
      </div>

      <q-separator />

      <div class="scroll col">
        <div
          v-for="(counter, index) in filtered_counters"
          :key="counter._key"
          class="row pointer q-px-lg q-py-xs medium full-width"
          :class="{
            'alternate-row': index % 2 === 0,
            'bg-blue-backdrop': counter._key === selected_counter_key,
          }"
          style="white-space: nowrap"
          @click="showCounterDetail(counter._key)"
        >
          <div class="col">
            {{ $capitalize(counter.name) }}
          </div>
          <div class="col-3">
            {{ $capitalize(counter.next_tick) }}
          </div>
        </div>
      </div>

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

    <BaseDialog :show="show_new_counter_form" :no-backdrop-dismiss="false">
      <CounterNew @close="show_new_counter_form = false" @created="getCounters">
      </CounterNew>
    </BaseDialog>

    <q-separator vertical />

    <!-- COUNTER DATA -->
    <div v-if="data_ready" class="col full-height">
      <router-view :counter="selected_counter" @reload="getCounters">
      </router-view>
    </div>
  </div>
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
