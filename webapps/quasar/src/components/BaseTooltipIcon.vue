<template>
  <div>
    <slot name="before"></slot>
  	<v-tooltip top :color="color" open-delay="200">
      <template v-slot:activator="{on}">
        <v-icon 
        	v-on="on" 
        	dense class="mx-2 hover-color"
        	:style="hoverColor"
          @click.stop="emit"
        	>{{ icon }}
        </v-icon>
      </template>
      <span>{{ tooltip | capitalize }}</span>
    </v-tooltip>
    <slot name="after"></slot>
  </div>
</template>

<script>
export default {

  name: 'BaseTooltipIcon',
  props: {
    icon: {
      type: String,
      required: true,
    },
    tooltip: {
      type: String,
      required: true,
    },    
    color: {
      type: String,
      default: 'grey'
    }
  },

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
  },

  methods: {

    /* 
    On the parent element, this allows to bubble up the click event correctly 
    with the event name equal to the tolltip text passed down
    */
    emit() {
      this.$emit('iconClick')
    }
  }
}
</script>

<style lang="css" scoped>
	.hover-color:hover {
		color: var(--hover-color);
	}
</style>