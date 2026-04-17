<template>
  <LoadingSignal v-if="!vuex_ready" />

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
          <div class="col-8 ellipsis">
            {{ $t('name') }}
          </div>
          <div class="col-4 ellipsis">
            {{ $t('code') }}
          </div>
        </div>

        <q-separator />

        <!-- OPERATION LIST -->
        <q-scroll-area class="col">
          <div
            v-for="(operation, index) in filtered_operations"
            :key="index"
            class="row pointer q-px-lg q-py-xs medium overflow-hidden"
            :class="{
              'alternate-row': index % 2 === 0,
              'bg-blue-backdrop': operation._key === selected_operation_key,
            }"
            @click="showOperationDetail(operation._key)"
          >
            <div class="col-8 ellipsis">
              {{ $capitalize(operation.name) }}
            </div>
            <div class="col-4 ellipsis">
              {{ operation.code }}
            </div>
          </div>
        </q-scroll-area>

        <q-separator />

        <!-- OPERATION LIST COUNT -->
        <div class="row flex-center smaller q-py-xs">
          {{ filtered_operations.length }} {{ $t('of') }}
          {{ operation_list.length }}
        </div>

        <div class="q-pa-md q-mt-auto">
          <q-btn
            class="full-width q-mt-auto"
            color="theme-blue"
            :label="$t('operation.add_op')"
            @click="openOperationNew"
          >
          </q-btn>
        </div>
      </div>
    </template>

    <template #after>
      <!-- OPERATION DATA -->
      <div class="col full-height">
        <router-view v-slot="{ Component, route }">
          <component :is="Component" v-if="route.name === 'operationNew'" />
          <component
            :is="Component"
            v-else-if="selected_operation"
            :operation="selected_operation"
          />
        </router-view>
      </div>
    </template>
  </q-splitter>
</template>

<script>
import LoadingSignal from '@/components/LoadingSignal.vue';
import multiMatch from '@/lib/MultiFieldSearch.js';

export default {
  name: 'OperationLibrary',

  components: { LoadingSignal },

  data() {
    return {
      vuex_ready: false,
      search_text: undefined,
      splitter_model: 30,
    };
  },

  computed: {
    operation_list() {
      return this.$store.state.process.operations;
    },

    selected_operation_key() {
      return this.$route.params.operation_key;
    },

    selected_operation() {
      return this.operation_list.find(
        (op) => op._key == this.selected_operation_key,
      );
    },

    filtered_operations() {
      const fields_to_search = ['name', 'code', 'description'];
      return this.operation_list.filter((op) =>
        multiMatch(this.search_text, op, fields_to_search),
      );
    },
  },

  created() {
    this.$store.dispatch('getOperations').then(() => {
      this.vuex_ready = true;
    });
  },

  methods: {
    showOperationDetail(operation_key) {
      this.$router.push({
        name: 'operationDetail',
        params: { operation_key },
      });
    },

    openOperationNew() {
      this.$router.push({ name: 'operationNew' });
    },
  },
};
</script>
