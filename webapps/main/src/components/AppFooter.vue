<template>
	<v-footer app fixed :color="$theme.black">
	  <v-row no-gutter class="align-center justify-space-between px-2">
	    <v-col class="text-left pa-0">
	    	<span class="display smaller">ESSEGI AUTOMATION - PROGRESS</span>
	    	<span class="material-icons smaller ml-2">info</span>
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
  	date() { return this.now.setLocale("it").toLocaleString(DateTime.DATE_HUGE) }
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
	font-size: .9em;
	vertical-align: bottom
}
</style>