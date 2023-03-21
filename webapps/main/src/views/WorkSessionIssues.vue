<template>
  <div class="q-pa-md">
    <q-list>
      <q-item
        v-for="issue in issues"
        :key="issue._key"
        class="q-pa-lg">
        <q-item-section avatar>
          <q-icon :name="issue.icon" size="lg" />
        </q-item-section>
        <q-item-section>
          <q-item-label class="weight-bold text-h4">
            {{ issue.title }} (ID {{ issue._key }})
          </q-item-label>
          <q-item-label class="text-low">
            {{ issue.description }}
          </q-item-label>
        </q-item-section>
        <q-item-section top class="display col-auto weight-bold text-uppercase">
          <q-chip :color="issue.badge.color">
            {{ issue.badge.text }}
          </q-chip>
        </q-item-section>
      </q-item>
      <q-separator spaced />
    </q-list>
  </div>
</template>

<script>
export default {

  name: 'WorkSessionIssues',

  props: {
    job_key: String // from router
  },

  data () {
    return {
      issues: []
    }
  },

  created() {
    this.$api.get('issue', { params: { job_key: this.job_key }})
    .then(resp => this.issues = resp.data.map(i => {
      let badge = !i.open
        ? { color: 'theme-grey', text: this.$t('closed') }
        : i.critical
        ? { color: 'theme-red', text: this.$t('critical') }
        : { color: 'theme-orange', text: this.$t('open') }

      return { ...i, badge }
    }))
  }
}
</script>

<style lang="css" scoped>
</style>
