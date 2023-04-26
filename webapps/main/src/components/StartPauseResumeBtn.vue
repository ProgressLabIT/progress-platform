<template>
  <q-btn
    class="fit"
    :style="`background-color: ${color}`"
    square
    @click="startPauseResumeJob().action()">
    <div class="row items-center absolute-full">
      <div class="col-1 offset-2">
        <q-icon size="lg" :name="j.active ? 'mdi-pause':'mdi-play'" />
      </div>
      <div class="display medium offset-1">
        {{ startPauseResumeJob().text }}
      </div>
    </div>
  </q-btn>
</template>

<script>
import { mapState } from 'vuex'

export default {

  name: 'StartPauseResumeBtn',

  computed: {
    j() {
      return this.$store.state.traceability.working_job_data
    },

    color() {
      return this.j.active ? this.$theme.grey + 'aa'
        : (this.j.critical ? this.$theme.red : this.$theme.blue) + 'aa'
    },
  },

  methods: {
    startPauseResumeJob() {
      const result = {
        text: null,
        action: null
      }

      if (this.j.active) {
        result.text = this.$t('job.pause').toUpperCase()
        result.action = () => this.$store.dispatch('pauseJob')
        return result
      }

      else {
        // Check if progress has already been made or user has already started
        if (this.j.stage == 'started' ) {
          result.text = this.$t('job.resume').toUpperCase()
          result.action = () => this.$store.dispatch('resumeJob')
          return result
        }
        else {
          result.text = this.$t('job.start').toUpperCase()
          result.action = () => this.$store.dispatch('startJob')
          return result
        }
      }
    }
  }
}
</script>

<style lang="css" scoped>
</style>
