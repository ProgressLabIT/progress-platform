<template>
  <v-card elevation="8" style="height: 250px">
    <v-container class="py-0 fill-height">
      <v-col cols="12" class="pa-1 fill-height d-flex flex-column">

        <!-- OP CODE/LINE -->
        <v-row class="text-uppercase">
          <v-col cols="auto" style="max-width: 60%">
            <h6 class="text-uppercase">{{ $tc("work_order.wo_code") }}</h6>
            <h4 class="display highlight text-truncate">{{ job.wo_code }}</h4>
          </v-col>
          <v-col cols="auto" class="text-right">
            <h6 class="text-uppercase">{{ $tc("work_order.wo_line.line_only", 1) }}</h6>
            <h4 class="display highlight">{{ job.wo_line }}</h4>
          </v-col>
          <v-spacer></v-spacer>
          <v-col cols="auto">
            <v-icon>{{ job.assigned ? 'mdi-account-check' : 'mdi-account-question' }}</v-icon>
          </v-col>
        </v-row>

        <!-- PRODUCT DATA -->
        <v-row justify="space-between">
          <v-col cols="12">
            <h6 class="text-uppercase">{{ $tc("product.label", 1) }}</h6>
            <h4 class="display highlight text-uppercase">{{ job.product_code }}</h4>
            <div class="body-2 text-truncate">{{ job.product_description }}</div>
          </v-col>
          <v-col cols="12">
            <h6 class="text-uppercase">{{ $tc("phase.short", 1) }}</h6>
            <h4 class="display highlight">{{ job.phase_alias }}</h4>
          </v-col>
        </v-row>

        <!-- <v-spacer></v-spacer> -->
          
        <!-- PROGRESS -->
        <v-row>
          <v-col cols="auto" class="text-uppercase">
            <h6 class="text-uppercase">{{ $tc("quantity.completed_total") }}</h6>
            <h4 class="display highlight">{{ job.qt_completed }} / {{ job.qt_planned }}</h4>
          </v-col>
          <v-col cols="auto" class="text-uppercase text-right ml-auto">
            <h6 class="text-uppercase">{{ $tc("progress") }}</h6>
            <h4 class="display highlight">{{ job.progress }}%</h4>
          </v-col>
        </v-row>

        <v-progress-linear 
          absolute bottom
          :value="job.progress"
          height="8px" 
          :color="$theme.blue">
        </v-progress-linear>  

      </v-col>  
      <!-- <v-overlay absolute opacity=".2" :value="true"></v-overlay> -->
    </v-container>
  </v-card>
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
