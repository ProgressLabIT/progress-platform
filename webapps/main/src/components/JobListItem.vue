<template>
  <q-item :class="{ 'text-low': job_data.stage == 'closed' }">
    <q-item-section avatar v-if="show_key">
      {{ job_data._key }}
    </q-item-section>
    <q-item-section v-if="show_assignee">
      <BaseUserAvatar
        v-if="job_data.assigned_to"
        :user="job_data.assigned_to">
      </BaseUserAvatar>
      <div v-else class="smaller">
        not assigned
      </div>
    </q-item-section>
    <q-item-section v-if="show_progress">
      <BaseProgressBar :data="job_data" />
    </q-item-section>
    <q-item-section side v-if="show_quantities">
      {{ job_data.qt_completed + '/' + job_data.qt_planned }}
    </q-item-section>
  </q-item>
</template>

<script>
import BaseProgressBar from '@/components/BaseProgressBar.vue'
import BaseUserAvatar from '@/components/BaseUserAvatar.vue'

export default {

  name: 'JobListItem',

  components: {
    BaseProgressBar,
    BaseUserAvatar
  },

  props: {
    job_data: {
      type: Object,
      required: true
    },
    show_key: {
      type: Boolean,
      default: true
    },
    show_phase: {
      type: Boolean,
      default: false
    },
    show_progress: {
      type: Boolean,
      default: false
    },
    show_assignee: {
      type: Boolean,
      default: true
    },
    show_quantities: {
      type: Boolean,
      default: true
    }
  }
}
</script>

<style lang="css" scoped>
</style>
