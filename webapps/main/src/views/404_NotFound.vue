<template>
  <v-container class="fill-height">
    <v-row class="fill-height" align="center" justify="center">
      <v-col cols="auto" class="text-center">
        <h1 class="display highlight">OOOOOPS!</h1>      
        <p class="mb-6">Questa pagina non esiste.</p>
       
        <v-btn block
          v-for="link in links"
          :key="link"
          class="mb-2" 
          :color="$theme.blue" 
          @click="$router.push({name: link})">
          {{ $t(`views.${link}`) }}
        </v-btn>
        <!-- <v-btn block :color="$theme.blue" @click="$router.push({name: 'productionOverview'})">
          Monitoraggio Produzione
        </v-btn> -->
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
export default {

  name: 'NotFound',

  data () {
    return {
      links: ['adminPanel', 'libraryRoot', 'productionRoot', 'operatorRoot']
    }
  }
}
</script>

<style lang="css" scoped>
</style>
