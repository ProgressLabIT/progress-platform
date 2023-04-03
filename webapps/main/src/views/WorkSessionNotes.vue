<template>
  <div class="fit column q-pa-md">
    <div v-if="no_notes">
      <NoDataAlert>{{ $t('notes_empty') }}</NoDataAlert>
    </div>
    <template v-else>
      <!-- WORK ORDER NOTES -->
      <div
        v-if="job.order_notes"
        class="surface2 full-width multiline-text q-mb-md q-pa-md"
        style="min-height: 100px">
        <div class="text-uppercase text-h5 q-mb-md">
          {{ $t('notes_order') }}
        </div>
        <div>{{ job.order_notes }}</div>
      </div>
      <!-- PHASE NOTES -->
      <div
        v-if="job.phase_notes"
        class="surface2 full-width multiline-text q-mb-md q-pa-md"
        style="min-height: 100px">
        <div class="text-uppercase text-h5 q-mb-md">
          {{ $t('notes_production') }}
        </div>
        <div>{{ job.phase_notes }}</div>
      </div>
      <!-- PRODUCT NOTES -->
      <div
        v-if="job.product_notes"
        class="surface2 full-width multiline-text q-pa-md"
        style="min-height: 100px">
        <div class="text-uppercase text-h5 q-mb-md">
          {{ $t('notes_product') }}
        </div>
        <div>{{ job.product_notes }}</div>
      </div>
    </template>
  </div>
</template>

<script>
import NoDataAlert from '@/components/NoDataAlert.vue'

export default {

  name: 'WorkSessionNotes',

  components: {
    NoDataAlert
  },

  props: {
    job: {
      type: Object,
      required: true
    }
  },

  data() {
    return {
      notes_fields: ['order_notes', 'phase_notes', 'product_notes'],
      notes_polling_instance: null
    }
  },

  computed: {
    no_notes() {
      return !this.job.order_notes
        && !this.job.phase_notes
        && !this.job.product_notes
    }
  },

  methods: {
    updateNotes() {
      this.$api.get(`job/${this.job._key}`).then(resp => {
        const new_job_data = resp.data.detail
        const changes = this.notes_fields.map(f => this.job[f] != new_job_data[f]).some(f => f == true)
        if (changes) {
          this.$store.commit('UPDATE_JOB_NOTES', new_job_data)
        }
      })
    }
  },

  created() {
    this.notes_polling_instance = setInterval(this.updateNotes, 5000)
  },

  beforeDestroy() {
    clearInterval(this.notes_polling_instance)
  }
}
</script>

<style lang="css" scoped>
</style>
