<template>
  <q-card
    class="q-pa-md row shadow-6 q-col-gutter-sm q-pb-lg q-pr-xl"
    :class="job.active ? 'bg-blue-backdrop' : 'surface1' "
    >

    <!-- WORK ORDER & PROJECT DATA -->
    <div class="col-3 column">
      <div class="col-auto">
        <div class="overline">
          {{ $t("work_order.list_headers.wo_code") }}
        </div>
        <div class="text-h4 display highlight text-truncate full-width ellipsis q-pr-sm">
          {{ job.wo_code }}
        </div>
      </div>
      <q-space></q-space>

      <div class="col-auto full-width">
        <div class="overline">
          {{ $t("project") }}
        </div>
        <div class="text-h4 display highlight full-width ellipsis">
          {{ job.project_code || '-' }}
        </div>
      </div>
    </div>


    <!-- PRODUCT & PHASE DATA  -->
    <div class="col-3">
      <div class="overline">
        {{ $t("product.code", 1) }}
      </div>
      <div class="text-h4 display highlight text-uppercase">
        {{ job.product_code }}
      </div>

      <div class="overline q-mt-lg">
        {{ $t("phase.short", 1) }}
      </div>
      <div class="text-h4 display highlight">
        {{ job.phase_alias }}
      </div>
    </div>

    <div class="col row items-center q-gutter-lg">
      <q-space></q-space>
      <q-btn
        outline
        round
        size="xl"
        :icon="job.active ? 'mdi-pause' : 'mdi-play'"
        :color="job.active ? 'theme-blue' : 'theme-grey'"
        @click.stop="toggleJob"
        />
    </div>

    <BaseProgressBar class="absolute-bottom" :data="job"></BaseProgressBar>
  </q-card>
</template>


<script setup>
import { ref } from 'vue'
import BaseProgressBar from '@/components/BaseProgressBar.vue'
import ProgressBtn from '@/components/ProgressBtn.vue'
import { useStore } from 'vuex'
import { timestamp } from '@/lib/TimeHandling.js'
import { api } from '@/boot/axios.js'

const props = defineProps({
  job: {
    type: Object,
    required: true
  }
})

const store = useStore()
const user_key = store.state.session.user._key

async function toggleJob() {

  const event_type =
      props.job.active ? 'JOB_PAUSED'
      : props.job.stage == 'created' ? 'JOB_STARTED'
      : 'JOB_RESUMED'

  const event_data = {
    timestamp: timestamp(),
    job_key: props.job._key,
    user_session_key: store.state.session._key,
    user_key,
    event_type
  }

  await api.post('event', event_data)
  await store.dispatch('loadJobAssignments', user_key)
}
</script>

<style lang="sass" scoped>
.glass

</style>
