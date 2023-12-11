<template>
  <div v-if="vuex_ready" class="row full-height">
    <div class="full-height column col-3">
      <q-input
        dense
        filled
        class="q-px-md q-pt-md"
        :placeholder="$capitalize($t('search'))"
        v-model="search_text"
      >
        <template #append>
          <q-icon name="mdi-magnify" />
        </template>
      </q-input>

      <div
        class="row q-mt-md q-px-lg q-py-sm text-h6 text-uppercase weight-bold"
      >
        <div class="col-8">
          {{ $t('name') }}
        </div>
        <div class="col-4">
          {{ $t('code') }}
        </div>
      </div>

      <q-separator />

      <!-- OPERATION LIST -->
      <div class="scroll col">
        <div
          v-for="(operation, index) in filtered_operations"
          class="row pointer q-px-lg q-py-xs medium"
          :class="{
            'alternate-row': index % 2 == 0,
            'bg-blue-backdrop': operation._key == selected_operation_key,
          }"
          :key="index"
          style="white-space: nowrap"
          @click="showOperationDetail(operation._key)"
        >
          <div class="col-8">
            {{ $capitalize(operation.name) }}
          </div>
          <div class="col-4">
            {{ operation.code }}
          </div>
        </div>
      </div>

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

    <q-separator vertical />

    <!-- OPERATION DATA -->
    <div class="col full-height">
      <router-view v-slot="{ Component, route }">
        <component v-if="route.name === 'operationNew'" :is="Component" />
        <component
          v-else-if="selected_operation"
          :is="Component"
          :operation="selected_operation"
        />
      </router-view>
    </div>
  </div>

  <LoadingSignal v-else />
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

  created() {
    this.$store.dispatch('getOperations').then(() => {
      this.vuex_ready = true;
    });
  },
};
</script>

<style lang="css" scoped></style>
