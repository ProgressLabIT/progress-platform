<template>
  <LoadingSignal v-if="!vuex_ready" />

  <div v-else class="row full-height">
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
        <div class="col-3">
          {{ $t('code') }}
        </div>
        <div class="col">
          {{ $t('name') }}
        </div>
        <div class="col-2 text-right">
          {{ $t('icon') }}
        </div>
      </div>

      <q-separator />

      <!-- ISSUE TYPE LIST -->
      <div class="scroll col">
        <div
          v-for="(issue_type, index) in filtered_issue_types"
          class="row pointer q-px-lg q-py-xs medium full-width"
          :class="{
            'alternate-row': index % 2 == 0,
            'bg-blue-backdrop': issue_type._key == selected_issue_type_key,
          }"
          :key="index"
          style="white-space: nowrap"
          @click="showIssueTypeDetail(issue_type._key)"
        >
          <div class="col-3">
            {{ $capitalize(issue_type.code) }}
          </div>
          <div class="col-8 ellipsis">
            {{ issue_type.name }}
          </div>
          <div class="col-1 text-right">
            <q-icon :name="issue_type.icon" />
          </div>
        </div>
      </div>

      <q-separator />

      <!-- ISSUE TYPE LIST COUNT -->
      <div class="row flex-center smaller q-py-xs">
        {{ filtered_issue_types.length }} {{ $t('of') }}
        {{ issue_type_list.length }}
      </div>

      <div class="q-pa-md q-mt-auto">
        <q-btn
          class="full-width q-mt-auto"
          color="theme-blue"
          :label="$t('new')"
          @click="openIssueTypeNew"
        >
        </q-btn>
      </div>
    </div>

    <q-separator vertical />

    <!-- ISSUE TYPE DATA -->
    <div class="col full-height" v-if="vuex_ready">
      <router-view v-slot="{ Component }">
        <component :is="Component" :issue_type="selected_issue_type" />
      </router-view>
    </div>
  </div>
</template>

<script>
import LoadingSignal from '@/components/LoadingSignal.vue';
import multiMatch from '@/lib/MultiFieldSearch.js';

export default {
  name: 'IssueTypeLibrary',

  components: { LoadingSignal },

  data() {
    return {
      vuex_ready: false,
      search_text: undefined,
    };
  },

  computed: {
    issue_type_list() {
      const issue_types = [...this.$store.state.quality.issue_types];
      issue_types.sort((a, b) =>
        a.code > b.code ? 1 : a.code < b.code ? -1 : 0,
      );
      return issue_types;
    },

    selected_issue_type_key() {
      return this.$route.params.issue_type_key;
    },

    selected_issue_type() {
      return this.issue_type_list.find(
        (it) => it._key == this.selected_issue_type_key,
      );
    },

    filtered_issue_types() {
      const fields_to_search = ['name', 'code', 'description'];
      return this.issue_type_list.filter((it) =>
        multiMatch(this.search_text, it, fields_to_search),
      );
    },
  },

  methods: {
    showIssueTypeDetail(issue_type_key) {
      this.$router.push({
        name: 'issueTypeDetail',
        params: { issue_type_key },
      });
    },

    openIssueTypeNew() {
      this.$router.push({ name: 'issueTypeNew' });
    },
  },

  created() {
    this.$store.dispatch('getIssueTypes').then(() => {
      this.vuex_ready = true;
    });
  },
};
</script>

<style lang="css" scoped></style>
