<template>
	<v-card height="190px" outlined elevation="4" class="surface-1">
		<v-img :src="`pics/products/${product.id}.jpeg`" class="fill">
			<v-sheet color="rgba(0,0,0,.7)" class="px-2 py-0">		  
		    <v-card-title class="display highlight ma-0 pa-0">
		      {{ product.code }}
		    </v-card-title>
		    
		    <!-- OPTION TO DISABLE TOOLTIP IF DESCRIPTION IS SHORTER THAN LIMIT: USABLE ONLY IF STRING IS TRUNCATED VIA JAVASCRIPT.
		    <v-tooltip content-class="no-transition" :disabled="product.description.length < desc_limit ? true : false" bottom max-width="40%">
		      <template v-slot:activator="{on}">
		        <v-card-subtitle v-on="on" class="mt-n4 pt-0 truncate-text">
		          {{ truncate(product.description, desc_limit, desc_trunc) }}
		        </v-card-subtitle>
		      </template> -->

		    <!-- CURRENT SETUP TRUNCATES DYNAMICALLY VIA CSS WITH ANY CARD WIDTH: SEE ALSO GLOBAL truncate-text CLASS-->
		    <v-tooltip content-class="no-transition" bottom max-width="40%">
		      <template v-slot:activator="{on}">
		        <v-card-subtitle v-on="on" class="px-0 pb-1 mt-n5 truncate-text">
		          {{ product.description }}
		        </v-card-subtitle>
		      </template>
		      <span>{{ product.description }}</span>
	    </v-tooltip>
 			</v-sheet>

	  </v-img>
  </v-card>  
</template>

<script>
export default {

  name: 'ProductCard',
  props: ['product'],

  data () {
    return {

    }
  }
}
</script>

<style lang="css" scoped>
</style>