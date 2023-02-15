<template>
  <q-card square style="height: 250px;" class="surface1 full-width shadow-8">
    <div class="column full-height justify-between q-pa-md q-pb-lg">

      <!-- OP CODE/LINE -->
      <div class="row full-width items-start text-uppercase q-mb-md">
        <div class="column col-auto q-pr-md" style="max-width: 60%">
          <div class="overline">
            {{ $t("work_order.list_headers.wo_code") }}
          </div>
          <div class="text-h4 display highlight text-truncate full-width ellipsis q-pr-sm">
            {{ job.wo_code }}
          </div>
        </div>
        <div class="column col">
          <div class="overline">
            {{ $t("project") }}
          </div>
          <div class="text-h4 display highlight full-width ellipsis q-pr-md">
            {{ job.project_code || '-' }}
          </div>
        </div>

        <q-space />

        <div class="col-auto text-right">
          <q-icon
            :name="job.assigned ? 'mdi-account-check' : 'mdi-account-question'"
            size="sm">
          </q-icon>
        </div>
      </div>

      <!-- PRODUCT DATA -->
      <div class="q-mb-md full-width">
        <div class="overline">{{ $t("product.label", 1) }}</div>
        <div class="text-h4 display highlight text-uppercase">{{ job.product_code }}</div>
        <div class="text-body2 ellipsis">{{ job.product_description }}</div>
      </div>

      <div class="q-mb-md">
        <div class="overline">{{ $t("phase.short", 1) }}</div>
        <div class="text-h4 display highlight">{{ job.phase_alias }}</div>
      </div>

      <!-- PROGRESS -->
      <div class="row text-uppercase justify-between">
        <div class="col-auto">
          <div class="overline">{{ $t("quantity.completed_total") }}</div>
          <div class="text-h4 display highlight">{{ job.qt_completed }} / {{ job.qt_planned }}</div>
        </div>
        <div class="col-auto text-right">
          <div class="overline">{{ $t("progress") }}</div>
          <div class="text-h4 display highlight">{{ job.progress }}%</div>
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
