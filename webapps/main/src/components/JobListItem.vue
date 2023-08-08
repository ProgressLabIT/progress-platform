<template>
  <q-item>
    <q-item-section avatar>
      {{ job_data._key }}
    </q-item-section>
    <q-item-section>
      <BaseUserAvatar
        v-if="job_data.assigned_to"
        :user="job_data.assigned_to">
      </BaseUserAvatar>
      <div v-else class="smaller">
        not assigned
      </div>
    </q-item-section>
    <q-item-section side>
      x {{ job_data.qt_completed + '/' + job_data.qt_planned }}
    </q-item-section>
  </q-item>
</template>

<script>
import BaseUserAvatar from '@/components/BaseUserAvatar.vue'

export default {

  name: 'JobListItem',

  components: {
    BaseUserAvatar
  },

  props: {
    job_data: {
      type: Object,
      required: true
    }
  }
}
</script>

<style lang="css" scoped>
</style>
