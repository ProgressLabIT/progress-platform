<template>
  <q-card
    class="q-pa-md shadow-6 q-pr-xl"
    :class="job.active ? 'bg-blue-backdrop' : 'surface1'"
  >
    <div class="row q-col-gutter-xl q-pb-sm">
      <div class="col col-md-6">
        <div class="row q-col-gutter-md">
          <div class="col-12 col-sm-5">
            <div class="overline">
              {{ $t('work_order.list_headers.wo_code') }}
            </div>
            <div class="text-h4 display highlight full-width ellipsis">
              {{ job.wo_code }}
            </div>
          </div>

          <div class="col-12 col-sm-7">
            <div class="overline q-mt-auto">
              {{ $t('project') }}
            </div>
            <div class="text-h4 display highlight full-width ellipsis">
              {{ job.project_code || '-' }}
            </div>
          </div>
        </div>

        <div class="q-my-lg"></div>

        <div class="overline">
          {{ $t('phase.short') }} - {{ $t('product.label', 1) }}
        </div>
        <div class="text-h4 display highlight text-uppercase">
          {{ job.phase_alias }} - {{ job.product_code }}
        </div>
        <div class="smaller text-low ellipsis-2-lines q-mt-xs">
          {{ job.product_description }}
        </div>
      </div>

      <div class="col-auto gt-xs">
        <div class="overline">
          <q-icon dense name="mdi-flag" class="q-pb-xs q-mr-xs"></q-icon>
          <span>AP - TOT</span>
        </div>
        <div class="text-h4 display highlight">
          {{ job.issues_open }} / {{ job.issues_total }}
        </div>

        <div class="q-my-lg"></div>

        <div class="overline">
          {{ $t('quantity.completed_total') }}
        </div>
        <div class="text-h4 q-mt-sm display column justify-center">
          {{ job.qt_completed }} / {{ job.qt_planned }}
        </div>
      </div>

      <q-space></q-space>

      <div class="col-auto column flex-center">
        <q-btn
          outline
          round
          size="xl"
          :icon="job.active ? 'mdi-pause' : 'mdi-play'"
          :color="job.active ? 'theme-blue' : 'theme-grey'"
          :class="{ 'animate-pulse': job.active }"
          @click.stop="toggleJob"
        />
      </div>
    </div>

    <BaseProgressBar class="absolute-bottom" :data="job"></BaseProgressBar>
  </q-card>
</template>

<script setup>
import { useStore } from 'vuex';
import BaseProgressBar from '@/components/BaseProgressBar.vue';
import { sendEvent } from '@/composables/event.js';

const props = defineProps({
  job: {
    type: Object,
    required: true,
  },
});

const store = useStore();
const user_key = store.state.session.user._key;

async function toggleJob() {
  const event_type = props.job.active
    ? 'JOB_PAUSED'
    : props.job.stage == 'created'
      ? 'JOB_STARTED'
      : 'JOB_RESUMED';

  await sendEvent({
    event_type,
    event_data: {
      job_key: props.job._key,
    }
  });
  await store.dispatch('loadJobAssignments', user_key);
}
</script>
