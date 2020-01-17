<template>
  <v-dialog
    value="true"
    fullscreen
    class="py-0">
    <v-card :color="$theme.black">
      <v-container fluid class="d-flex flex-column pt-2 px-5" style="height:100vh"> 
        <v-row dense justify="start" align="center" class="my-0 pl-1 flex-grow-0">

          <!-- SCREEN HEADER -->
          <v-icon small @click="$router.push(previousPage)">close</v-icon>
          <span class="ml-4 display medium highlight weight-medium">{{ title }} {{ item_key }}</span>
          
          <!-- DYNAMIC INTERNAL LINKS -->
          <v-col cols="auto" class="ml-auto">
            <v-tabs 
              active-class="weight-bold"
              background-color="transparent"
              :color="$theme.whitehigh"
              hide-slider right
              >
              <v-tab 
                v-for="(page, index) in links" 
                :key="index" 
                :to="`/product/${item_key}/${page}`"
                class="display" >
                <span >{{ page }}</span>
              </v-tab>
            </v-tabs>
          </v-col>  
        </v-row>  

        <!-- WINDOW CONTAINER -->
        <v-card outlined tile class="flex-grow-1 scroll" :style="'background-color:' + $theme.background">
            <router-view :item_key="item_key"></router-view>
        </v-card>

      </v-container>
    </v-card>
  </v-dialog>
</template>

<script>
export default {

  name: 'ModalScreen',
  props: [
    'item_key',    // route param from url
    'title',          // from parent prop
    'links'           // from parent prop
  ],

  data() {
    return {
      previousPage: '',
    };
  },

  beforeRouteEnter (to, from, next) {
    next(component => {
      component.previousPage = from.path
    })
  }
};
</script>

<style lang="css" scoped>
</style>
