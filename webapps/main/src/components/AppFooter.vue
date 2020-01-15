<template>
	<v-footer fixed>
	  <v-row cols=12 class="align-center justify-space-between my-0 py-0 px-2">
	    <v-col class="text-left pa-0">
	    	<span class="display smaller">ACME CORP - PROGRESS</span>
	    	<span class="material-icons smaller ml-1">info</span>
	    	<!-- <v-icon size="18" class="smaller ml-1">info</v-icon> -->
	    </v-col>
	    <v-col cols="1" class="text-center pa-0">
	    	<span class="display smaller">{{ time }}</span>
	    </v-col>
	    <v-col class="text-right pa-0">
				<span class="display smaller">{{ date }}</span>
			</v-col>
	  </v-row>
	</v-footer>
</template>

<script>
import {DateTime} from 'luxon'

export default {

  name: 'AppFooter',

  data () {
    return {
    	now: 0
    }
  },

  computed: {
  	time() { return this.now.toLocaleString(DateTime.TIME_SIMPLE) },
  	date() { return this.now.toLocaleString(DateTime.DATE_HUGE) }
  },

  created() {
  	this.now = DateTime.local()
  	setInterval(() => {
  		this.now = this.now.plus({seconds: 1})
  	}, 1000)
  }

}
</script>

<style lang="css" scoped>
.material-icons.smaller {
	font-size: .8em;
	vertical-align: middle
}
</style>