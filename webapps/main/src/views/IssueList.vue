<template>
  <div class="q-pa-md absolute-full scroll">
    <q-list v-if="issues.length">
      <template v-for="issue, index in issues" :key="index">
        <q-separator inset v-if="index > 0" />
        <IssueHeader
          clickable
          :issue="issue"
          @click="openIssue(issue._key)"
          @type-change="getIssues">
        </IssueHeader>
      </template>
    </q-list>
    <NoDataAlert v-else>
      {{ $t('issue_missing') }}
    </NoDataAlert>
    <router-view />
  </div>
</template>

<script>
import enrichIssue from '@/mixins/issues.js'
import IssueHeader from '@/components/IssueHeader.vue'
import NoDataAlert from '@/components/NoDataAlert.vue'

export default {

  name: 'IssueList',

  components: {
    IssueHeader,
    NoDataAlert
  },

  mixins: [enrichIssue],

  props: {
    // from router
    job_key: String,
    wo_key: String,
  },

  computed: {
    context() {
      // Check where the component is being used
      return this.job_key
        ? 'job'
        : this.wo_key
        ? 'work-order'
        : undefined
    },

    base_issues() {
      return this.$store.state.quality.issues
    },
    issues() {
      return this.base_issues.map(i => this.enrichIssue(i))
    }
  },

  methods: {
    openIssue(issue_key) {
      const next_route_name =
        this.context == 'job' ? 'jobIssueDetail'
        : this.context == 'work-order' ? 'workOrderIssueDetail'
        : null

      this.$router.push({
        name: next_route_name,
        params: { issue_key }
      })
    },

    getIssues() {
      const filter =
        this.context == 'job' ? { job_key: this.job_key }
        : this.context == 'work-order' ? { work_order_key: this.wo_key }
        : null

      this.$store.dispatch('getIssues', filter)
    }
  },

  created() {
    this.getIssues()
  }
}
</script>

<style lang="css" scoped>
</style>
