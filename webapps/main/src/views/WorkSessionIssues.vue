<template>
  <div class="q-pa-md absolute-full scroll">
    <q-list>
      <template v-for="issue, index in issues" :key="index">
        <q-separator inset v-if="index > 0" />
        <IssueHeader clickable :issue="issue" @click="openIssue(issue._key)"/>
      </template>
    </q-list>
    <router-view />
  </div>
</template>

<script>
import IssueHeader from '@/components/IssueHeader.vue'
import enrichIssue from '@/mixins/issues.js'

export default {

  name: 'WorkSessionIssues',

  components: {
    IssueHeader
  },

  mixins: [enrichIssue],

  props: {
    job_key: String // from router
  },

  computed: {
    issues() {
      return this.$store.state.quality.issues.map(i => this.enrichIssue(i))
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
