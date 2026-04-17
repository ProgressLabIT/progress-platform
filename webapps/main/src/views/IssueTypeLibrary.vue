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
          <div class="col-3 ellipsis">
            {{ $t('code') }}
          </div>
          <div class="col ellipsis">
            {{ $t('name') }}
          </div>
          <div class="col-2 text-right ellipsis">
            {{ $t('icon') }}
          </div>
        </div>

        <q-separator />

        <!-- ISSUE TYPE LIST -->
        <q-scroll-area class="col">
          <div
            v-for="(issue_type, index) in filtered_issue_types"
            :key="index"
            class="row pointer q-px-lg q-py-xs medium overflow-hidden"
            :class="{
              'alternate-row': index % 2 === 0,
              'bg-blue-backdrop': issue_type._key === selected_issue_type_key,
            }"
            @click="showIssueTypeDetail(issue_type._key)"
          >
            <div class="col-3 ellipsis">
              {{ $capitalize(issue_type.code || '') }}
            </div>
            <div class="col-8 ellipsis">
              {{ issue_type.name }}
            </div>
            <div class="col-1 text-right">
              <q-icon :name="issue_type.icon" />
            </div>
          </div>
        </q-scroll-area>

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
    </template>

    <template #after>
      <!-- ISSUE TYPE DATA -->
      <div class="col full-height">
        <router-view v-slot="{ Component }">
          <component :is="Component" :issue-type="selected_issue_type" />
        </router-view>
      </div>
    </template>
  </q-splitter>
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
      splitter_model: 30,
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
      return this.$route.params.issueTypeKey;
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

  created() {
    this.$store.dispatch('getIssueTypes').then(() => {
      this.vuex_ready = true;
    });
  },

  methods: {
    showIssueTypeDetail(issueTypeKey) {
      this.$router.push({
        name: 'issueTypeDetail',
        params: { issueTypeKey },
      });
    },

    openIssueTypeNew() {
      this.$router.push({ name: 'issueTypeNew' });
    },
  },
};
</script>
