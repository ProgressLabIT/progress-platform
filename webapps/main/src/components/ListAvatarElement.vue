<template>
    <v-list-item>
	    <v-list-item-avatar v-if="src">
		  <slot name="avatar">
		  	<v-img :src="src"></v-img>
		  </slot>
		</v-list-item-avatar>
		
		<v-list-item-content>

		  <v-list-item-title class="highlight">
		  	<slot name="title">
		  		{{ title }}
		  	</slot>
		  </v-list-item-title>
		  
		  <v-list-item-subtitle class="body-2">
		  	<slot name="subtitle">
		  		{{ subtitle }}
		  	</slot>
		  </v-list-item-subtitle>

		</v-list-item-content>
	</v-list-item>
</template>

<script>
export default {

  name: 'ListAvatarElement',

  props: ['src', 'title', 'subtitle']
}
</script>

<style lang="css" scoped>
</style>