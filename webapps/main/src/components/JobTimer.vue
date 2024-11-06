<template>
  <div>
    <q-linear-progress
    animation-speed="300"
    :value="Math.min(timerProgress, 1)"
    :color="color.foreground"
    :track-color="color.background"
    :buffer="1"
    :size="size"
    />
    <div class="row justify-between items-center q-pt-xs">
      <div class="text-h5 weight-bold text-uppercase">
        {{ $t('processing_time') }}
      </div>
      <div>
        {{ $durationFromMillisec(elapsed, {precision: 'm'}) }} /
        {{ $durationFromMillisec(jobTargetTime, {precision: 'm'}) }}
      </div>
    </div>
  </div>
</template>

<script>
import { mapState } from 'vuex';

export default {
  name: 'JobTimer',

  props: {
    size: {
      type: String,
      default: '4px',
    },
  },

  data() {
    return {
      elapsed: undefined,
      timer_instance: undefined,
    }
  },

  computed: {
    ...mapState({
      j: (state) => state.traceability.working_job_data,
    }),

    jobTargetTime() {
      return this.j.parameters.std_processing_time * this.j.qt_planned * 1000
    },

    timerProgress() {
      return this.elapsed / this.jobTargetTime
    },

    color() {
      const background = this.j.active
        ? this.timerProgress > 1
          ? 'orange-backdrop'
          : 'blue-backdrop'
        : 'grey-backdrop';
      const foreground =
        this.timerProgress > 1
          ? this.j.active
            ? 'theme-orange'
            : 'orange-backdrop'
          : this.j.active
            ? 'theme-blue'
            : 'theme-grey';
      return { foreground, background };
    },
  },

  mounted() {
    if (this.j.parameters.display_job_timer) {
      this.updateTimer()
      this.timer_instance = setInterval(this.updateTimer, 10000)
    }
  },

  onBeforeUnload() {
    clearInterval(this.timer_instance)
  },

  methods: {
    updateTimer() {
      // Fetch time only if job is active
      if (this.j.active) {
        this.$api.get(`/job/${this.j._key}/time`).then((resp) => {
          this.elapsed = resp.data.detail
        })
      }
    }
  },
};
</script>
