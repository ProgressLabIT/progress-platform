<template>
  <v-container class="fill-height">
    <v-row class="fill-height" align="center" justify="center">
      <v-col cols="auto" class="text-center">
        <h1 class="display highlight">OOOOOPS!</h1>      
        <p>Questa pagina non esiste.</p>
        <v-btn block class="mt-6 mb-2" :color="$theme.blue" @click="$router.push({name: 'productList'})">
          Libreria prodotti
        </v-btn>
        <v-btn block :color="$theme.blue" @click="$router.push({name: 'productionOverview'})">
          Monitoraggio Produzione
        </v-btn>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
export default {

  name: 'NotFound',

  data () {
    return {

    }
  }
}
</script>

<style lang="css" scoped>
</style>