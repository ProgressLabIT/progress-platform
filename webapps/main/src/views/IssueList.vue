<template>
  <div class="q-pa-md absolute-full scroll">
    <q-list v-if="issues.length">
      <template v-for="(issue, index) in issues" :key="index">
        <q-separator v-if="index > 0" inset />
        <IssueHeader
          clickable
          :issue="issue"
          @click="openIssue(issue._key)"
          @type-change="getIssues"
        >
        </IssueHeader>
      </template>
    </q-list>
    <NoDataAlert v-else>
      {{ $t('issue_missing') }}
    </NoDataAlert>
    <template v-if="$route.name == 'workOrderIssues'">
      <q-btn
        round
        color="theme-blue"
        icon="mdi-plus"
        class="fixed-bottom-right q-mr-xl q-mb-xl"
        size="16px"
        @click="show_form = true"
      >
      </q-btn>
      <IssueForm
        :show="show_form"
        mode="new"
        with_links
        auto_link_mode="work_order"
        :auto_links="{ work_order: wo_data }"
        @close="show_form = false"
        @issue-created="getIssues"
      >
      </IssueForm>
    </template>

    <router-view />
  </div>
</template>

<script>
import IssueForm from '@/components/IssueForm.vue';
import IssueHeader from '@/components/IssueHeader.vue';
import NoDataAlert from '@/components/NoDataAlert.vue';
import enrichIssue from '@/mixins/issues.js';

export default {
  name: 'IssueList',

  components: {
    IssueForm,
    IssueHeader,
    NoDataAlert,
  },

  mixins: [enrichIssue],

  props: {
    // from route
    jobKey: {
      type: String,
      default: undefined,
    },
    wo_key: {
      type: String,
      default: undefined,
    },

    // from component at parent route
    job: {
      type: Object,
      default: undefined,
    },
    wo_data: {
      type: Object,
      default: undefined,
    },
  },

  data() {
    return {
      show_form: false,
    };
  },

  computed: {
    context() {
      // Check where the component is being used
      return this.jobKey ? 'job' : this.wo_key ? 'work-order' : undefined;
    },

    work_order_key() {
      return this.context == 'job' ? this.job.wo_key : this.wo_key ?? null;
    },

    base_issues() {
      return this.$store.state.quality.issues;
    },
    issues() {
      return this.base_issues.map((i) => this.enrichIssue(i));
    },
  },

  created() {
    this.getIssues();
  },

  methods: {
    openIssue(issueKey) {
      const next_route_name =
        this.context === 'job'
          ? 'jobIssueDetail'
          : this.context === 'work-order'
            ? 'workOrderIssueDetail'
            : null;

      this.$router.push({
        name: next_route_name,
        params: { issueKey },
      });
    },

    getIssues() {
      this.$store.dispatch('getIssues', {
        work_order_key: this.work_order_key,
      });
    },
  },
};
</script>

<style lang="css" scoped></style>
