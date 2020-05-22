<template>
  <v-container fluid class="fill pt-0 d-flex flex-column">      
      
      <!-- TAB LINKS -->
      <v-row dense class="flex-grow-0 mb-2">    
        <v-tabs
          background-color="transparent"
          v-model="current_view"
          :color="$theme.white_high"
          hide-slider
          class="flex-shrink-1 flex-grow-0">
          <v-tab 
            v-for="(view, index) in admin_views"
            :key="index"
            :to="{ name: view.route_name }"
            class="display">
            {{ view.name }}
          </v-tab>
        </v-tabs>
      </v-row>

        <!-- MAIN CONTENT -->
        <div class="scroll flex-grow-1">
          <router-view></router-view>
        </div>
          
  </v-container>
</template>

<script>
export default {

  name: 'AdminSection',

  data () {
    return {
      current_view: 0,
      admin_views: [
        {
          name: 'Utenti',
          component: 'UserLibrary',
          route_name: 'userLibrary'
        }
      ]
    }
  },
}
</script>

<style lang="css" scoped>
</style>