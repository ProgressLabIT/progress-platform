<template>
  <q-card square style="height: 250px;" class="surface1">
    <div class="column full-height justify-between q-pa-md q-pb-lg">

      <!-- OP CODE/LINE -->
      <div class="row items-start text-uppercase q-mb-md">
        <div class="column col-auto q-mr-xl" style="max-width: 60%">
          <div class="overline">{{ $t("work_order.wo_code") }}</div>
          <div class="text-h4 highlight text-truncate">{{ job.wo_code }}</div>
        </div>
        <div class="column col-auto text-right">
          <div class="overline">{{ $t("work_order.wo_line.line_only", 1) }}</div>
          <div class="text-h4 highlight">{{ job.wo_line }}</div>
        </div>

        <q-space />

        <div class="col-auto">
          <q-icon
            :name="job.assigned ? 'mdi-account-check' : 'mdi-account-question'"
            size="sm">
          </q-icon>
        </div>
      </div>

      <!-- PRODUCT DATA -->
      <div class="row justify-between q-mb-md">
        <div class="col-12">
          <div class="overline">{{ $t("product.label", 1) }}</div>
          <div class="text-h4 highlight text-uppercase">{{ job.product_code }}</div>
          <div class="text-body2 text-truncate">{{ job.product_description }}</div>
        </div>
      </div>

      <div class="row justify-between q-mb-md">
        <div class="col-12">
          <div class="overline">{{ $t("phase.short", 1) }}</div>
          <div class="text-h4 highlight">{{ job.phase_alias }}</div>
        </div>
      </div>

      <!-- PROGRESS -->
      <div class="row text-uppercase justify-between">
        <div class="col-auto">
          <div class="overline">{{ $t("quantity.completed_total") }}</div>
          <div class="text-h4 highlight">{{ job.qt_completed }} / {{ job.qt_planned }}</div>
        </div>
        <div class="col-auto text-right">
          <div class="overline">{{ $t("progress") }}</div>
          <div class="text-h4 highlight">{{ job.progress }}%</div>
        </div>
      </div>
    </div>

    <q-linear-progress
      :value="job.progress / 100"
      size="8px"
      color="theme-blue"
      track-color="blue-backdrop"
      class="absolute-bottom">
    </q-linear-progress>

  </q-card>
</template>

<script>
export default {

  name: 'JobCard',

  props: {
    job: {
      type: Object,
      required: true
    },
    background: {
      type: String,
    }
  }
}
</script>

<style lang="css" scoped>
</style>
