<template>
  <q-item class="q-pa-lg" :clickable="clickable">
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
  }
}
</script>

<style lang="css" scoped>
</style>
