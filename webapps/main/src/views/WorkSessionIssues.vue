<template>
  <div class="q-pa-md absolute-full scroll">
    <q-list v-if="issues.length">
      <template v-for="issue, index in issues" :key="index">
        <q-separator inset v-if="index > 0" />
        <IssueHeader clickable :issue="issue" @click="openIssue(issue._key)"/>
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

  name: 'WorkSessionIssues',

  components: {
    IssueHeader,
    NoDataAlert
  },

  mixins: [enrichIssue],

  props: {
    job_key: String // from router
  },

  computed: {
    base_issues() {
      return this.$store.state.quality.issues
    },
    issues() {
      return this.base_issues.map(i => this.enrichIssue(i))
    }
  },

  methods: {
    openIssue(issue_key) {
      this.$router.push({
        name: 'jobIssueDetail',
        params: { issue_key }
      })
    }
  },

  created() {
    this.$store.dispatch('getIssues', { job_key: this.job_key })
  }
}
</script>

<style lang="css" scoped>
</style>
