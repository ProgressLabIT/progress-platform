<template>
  <v-card elevation="8" height="250px" :color="background ? background : $theme.surface1">
    <v-container class="py-0 fill-height">
      <v-col cols="12" class="pa-1 fill-height d-flex flex-column">

        <!-- OP CODE/LINE -->
        <v-row class="text-uppercase">
          <v-col cols="auto">
            <h5>CODICE OP</h5>
            <h3 class="display highlight">{{ job.wo_code }}</h3>
          </v-col>
          <v-col cols="auto" class="text-right">
            <h5>RIGA</h5>
            <h3 class="display highlight">{{ job.wo_line }}</h3>
          </v-col>
        </v-row>

        <!-- PRODUCT DATA -->
        <v-row>
          <v-col cols="12">
            <h5>PRODOTTO</h5>
            <h3 class="display highlight text-uppercase">{{ job.product_code }}</h3>
            <div class="body-2">{{ job.product_description }}</div>
          </v-col>
        </v-row>

        <!-- <v-spacer></v-spacer> -->
          
        <!-- PROGRESS -->
        <v-row>
          <v-col cols="auto" class="text-uppercase">
            <h5>QT COMPL. - TOT.</h5>
            <h3 class="display highlight">{{ job.qt_completed }} / {{ job.qt_planned }}</h3>
          </v-col>
          <v-col cols="auto" class="text-uppercase text-right ml-auto">
            <h5>AVANZAMENTO</h5>
            <h3 class="display highlight">{{ job.progress }}%</h3>
          </v-col>
        </v-row>

        <v-progress-linear 
          absolute bottom
          :value="job.progress"
          height="8px" 
          :color="$theme.blue">
        </v-progress-linear>  

      </v-col>  
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