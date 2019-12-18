<template>
	<v-tooltip top :color="color">
    <template v-slot:activator="{on}">
      <v-icon 
      	v-on="on" 
      	dense class="mx-2 hover-color"
      	:style="hoverColor"
      	>{{ icon }}</v-icon>
      </template>
    <span>{{ tooltip }}</span>
  </v-tooltip>
</template>

<script>
export default {

  name: 'TooltipIcon',
  props: ['icon', 'tooltip', 'color'],
  data () {
    return {
    }
  },
  computed: {
  	hoverColor() {
  		return {
  			'--hover-color': this.color
  		}
  	}
  }
}
</script>

<style lang="css" scoped>
	.hover-color:hover {
		color: var(--hover-color);
	}
</style>