<template>
  <q-card square style="height: 280px;" class="surface1 full-width shadow-8">
    <div class="column q-col-gutter-md full-height justify-between q-px-md q-pt-md">

      <!-- WO CODE -->
      <div class="row col-auto justify-start q-col-gutter-sm">
        <div class="column col-auto" style="max-width: 60%">
          <div class="overline">
            {{ $t("work_order.list_headers.wo_code") }}
          </div>
          <div class="text-h4 display highlight text-truncate full-width ellipsis q-pr-sm">
            {{ job.wo_code }}
          </div>
          </div>

        <!-- PROJECT CODE -->
        <div class="column col-auto">
          <div class="overline">
            {{ $t("project") }}
          </div>
          <div class="text-h4 display highlight full-width ellipsis">
            {{ job.project_code || '-' }}
          </div>
        </div>

        <q-space></q-space>
        <div class="col-auto text-right">
          <q-icon
            :name="job.assigned ? 'mdi-account-check' : 'mdi-account-question'"
            size="sm">
          </q-icon>
        </div>

      </div>





      <!-- PRODUCT DATA -->
      <div class="column col-auto">
        <div class="overline">{{ $t("product.label", 1) }}</div>
        <div class="text-h4 display highlight text-uppercase">{{ job.product_code }}</div>
        <div class="text-body2 ellipsis">{{ job.product_description }}</div>
      </div>

      <div class="column col-auto">
        <div class="overline">{{ $t("phase.short", 1) }}</div>
        <div class="text-h4 display highlight">{{ job.phase_alias }}</div>
      </div>

      <!-- PROGRESS -->
      <div class="row col-auto text-uppercase justify-between">
        <div class="col-auto">
          <div class="overline">{{ $t("quantity.completed_total") }}</div>
          <div class="text-h4 display highlight">
            {{ job.qt_completed }} / {{ job.qt_planned }}
          </div>
        </div>
        <div class="col-auto text-right overline">
          <div class="overline">
            <q-icon dense name="mdi-flag" class="q-pb-xs"></q-icon> aperte
          </div>
          <div class="text-h4 display highlight">
            {{ job.issue_count }}
          </div>
        </div>
        <div class="col-auto text-right">
          <div class="overline">
            {{ $t("progress") }}
          </div>
          <div class="text-h4 display highlight">
            {{ job.progress }}%
          </div>
        </div>
      </div>
    </div>

    <BaseProgressBar
      :data="job"
      size="8px"
      class="absolute-bottom">
    </BaseProgressBar>

  </q-card>
</template>

<script>
import BaseProgressBar from '@/components/BaseProgressBar.vue'

export default {

  name: 'JobCard',

  components: {
    BaseProgressBar
  },

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
