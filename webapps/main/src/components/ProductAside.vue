<template>
  <div class="fill-height d-flex flex-column">
   <!-- PRODUCT IMAGE -->
    <v-card outlined :img="`/media/product/${product._key}/image.jpeg`" height="30vh"/> 
    
    <!-- PRODUCT CODE -->
    <h4 class="weight-bold medium mt-6 text-uppercase">
      {{ $t('product.code') }}
    </h4>
    <h1 class="display highlight">{{ product.code }}</h1>

    <!-- PRODUCT DESCRIPTION -->
    <h4 class="weight-bold medium mt-10 text-uppercase">
      {{ $t('description') }}
    </h4>
    <h3 class="highlight mt-1">{{ product.description }}</h3>      

    <v-spacer></v-spacer>
    <!-- PRODUCT TAGS -->
    <h4 class="weight-bold medium">TAG</h4>
    <v-row justify="start" class="mx-0 pt-2">            
      <v-chip small
        v-for="tag in product.tags" 
        :key="tag"
        class="mr-2"
        >
      {{ tag }}
    </v-chip>
    </v-row>  
  </div>
</template>

<script>
export default {

  name: 'ProductAside',

  props: ['product'],

};
</script>

<style lang="css" scoped>
</style>
