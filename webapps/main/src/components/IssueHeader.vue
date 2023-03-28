<template>
  <q-item class="q-py-md" :clickable="clickable">
    <q-item-section avatar>
      <q-icon :name="icon" size="lg" />
    </q-item-section>
    <q-item-section>
      <q-item-label class="weight-bold text-h4">
        {{ issue._key }}
      </q-item-label>
    </q-item-section>
    <q-item-section top class="display col-auto weight-bold text-uppercase">
      <q-chip :color="issue.badge.color">
        {{ issue.badge.text }}
      </q-chip>
    </q-item-section>
  </q-item>
</template>

<script>
export default {

  name: 'IssueHeader',

  props: {
    issue: {
      type: Object,
      required: true
    },
    clickable: {
      type: Boolean,
      default: false
    }
  },

  computed: {
    icon() {
      return this.issue.icon || 'mdi-help'
    }
  }
}
</script>

<style lang="css" scoped>
</style>
