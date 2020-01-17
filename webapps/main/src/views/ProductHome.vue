<template>
  <v-container fill-height fluid>
    <v-row class="fill-height mx-0">
      
      <!-- LEFT COLUMN -->
      <v-col cols="4" class="d-flex flex-column">

        <!-- PRODUCT IMAGE -->
        <v-card outlined :img="`/pics/products/${item_key}.jpeg`" height="30vh"/> 
        
        <!-- PRODUCT CODE -->
        <h4 class="weight-bold medium mt-6">CODICE PRODOTTO</h4>
        <h1 class="display highlight">{{ product_data.code }}</h1>

        <!-- PRODUCT DESCRIPTION -->
        <h4 class="weight-bold medium mt-10">DESCRIZIONE</h4>
        <h3 class="highlight mt-1">{{ product_data.description }}</h3>      

        <v-spacer></v-spacer>
        <!-- PRODUCT TAGS -->
        <h4 class="weight-bold medium">TAG</h4>
        <v-row justify="start" class="mx-0 pt-2">            
          <v-chip small
            v-for="tag in product_data.tags" 
            :key="tag"
            class="mr-2"
            >
          {{ tag }}
        </v-chip>
        </v-row>  


        <!-- <v-select solo flat background-color="transparent"
           multiple single-line small-chips
          :items="product_data.tags"
          v-model="value"
          label="label"
        ></v-select> -->
      </v-col>  
    
      <!-- PRODUCT DATA -->
      <v-col cols="8" class="pa-0 pl-3">
        <v-container>
          <v-row class="mt-n3 pr-0">
            
            <!-- PARAMETERS -->
            <v-col cols="6">
              <v-card flat height="35vh"> 
                <v-container class="px-5 py-4">                  
                  <h4 class="display medium highlight">Parametri</h4>
                </v-container>
              </v-card>
            </v-col>  

            <!-- DOCS -->
            <v-col cols="6">
              <v-card flat height="35vh"> 
                <v-container class="px-5 py-4">                  
                  <h4 class="display medium highlight">documenti</h4>
                </v-container>
              </v-card>
            </v-col>  

            <!-- KPIs -->
            <v-col cols="6">
              <v-card flat height="35vh"> 
                <v-container class="px-5 py-4">                  
                  <h4 class="display medium highlight">indicatori</h4>
                </v-container>
              </v-card>
            </v-col>  

            <!-- ISSUES -->
            <v-col cols="6">
              <v-card flat height="35vh"> 
                <v-container class="px-5 py-4">                  
                  <h4 class="display medium highlight">segnalazioni</h4>
                </v-container>
              </v-card>
            </v-col>  
          </v-row>  
          
          <!-- PRODUCT ACTIONS -->
          <v-row>
            <v-spacer></v-spacer>
            <v-col cols="auto">
              <v-btn :color="$theme.blue">Crea ordine</v-btn>
            </v-col>  
            <v-col cols="auto">
              <v-btn :color="$theme.blue">Crea segnalazione</v-btn>
            </v-col>  
            <v-col cols="auto">
              <v-btn :color="$theme.red">Elimina</v-btn>
            </v-col>  
          </v-row>  
        </v-container>
      </v-col>

    </v-row>  
  </v-container>
</template>

<script>
import {api} from '@/lib/apiCall.js'

export default {

  name: 'ProductHome',

  props: ['item_key'],


  data() {
    return {
      product_data: {}
    };
  },

  created() {
    api
      .get('product/'+this.item_key)
      .then(resp => {
        console.log({resp})
        this.product_data = resp.data
      })
  }

};
</script>

<style lang="css" scoped>
</style>
