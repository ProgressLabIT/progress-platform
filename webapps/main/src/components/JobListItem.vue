<template>
  <q-item :class="{ 'text-low': jobData.stage === 'closed' }">
    <q-item-section v-if="showKey" avatar>
      {{ jobData._key }}
    </q-item-section>
    <q-item-section v-if="showAssignee">
      <BaseUserAvatar v-if="jobData.assigned_to" :user="jobData.assigned_to">
      </BaseUserAvatar>
      <div v-else class="smaller">not assigned</div>
    </q-item-section>
    <q-item-section v-if="showProgress">
      <BaseProgressBar :data="jobData" />
    </q-item-section>
    <q-item-section v-if="showQuantities" side>
      {{ jobData.qt_completed + '/' + jobData.qt_planned }}
    </q-item-section>
  </q-item>
</template>

<script>
import BaseProgressBar from '@/components/BaseProgressBar.vue';
import BaseUserAvatar from '@/components/BaseUserAvatar.vue';

export default {
  name: 'JobListItem',

  components: {
    BaseProgressBar,
    BaseUserAvatar,
  },

  props: {
    jobData: {
      type: Object,
      required: true,
    },
    showKey: {
      type: Boolean,
      default: true,
    },
    showProgress: {
      type: Boolean,
      default: false,
    },
    showAssignee: {
      type: Boolean,
      default: true,
    },
    showQuantities: {
      type: Boolean,
      default: true,
    },
  },
};
</script>
