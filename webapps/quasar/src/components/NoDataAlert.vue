<template>
  <v-container class="fill">
     <v-row justify="center" align="center" class="fill-height">
      <v-col class="text-center">
        <v-icon x-large :color="$theme.text_low">
          error_outline
        </v-icon>
        <div class="text-center mt-6 text-uppercase">
          <h3><slot>No data</slot></h3>
        </div>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
export default {

  name: 'NoDataAlert',

}
</script>

<style lang="css" scoped>
</style>
