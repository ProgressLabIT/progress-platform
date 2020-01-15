<template>
  <v-dialog
    value="true"
    fullscreen
    class="py-0">
    <v-card :color="$theme.background">
      <v-container fluid class="d-flex flex-column pt-2 px-5" style="height:100vh"> 
        <v-row dense justify="start" align="center" class="my-0 pl-1 flex-grow-0">
          <v-icon small @click="$router.push(previousPage)">close</v-icon>
          <span class="ml-4 display medium highlight weight-medium">TITLE</span>
          <v-col cols="auto" class="ml-auto">
            <!-- <router-link v-for="(page, index) in links" :key="index" :to="page" class="display mx-2">
              {{ page }}
            </router-link> -->
            <v-tabs 
              v-model="activePageIndex"
              active-class="weight-bold"
              background-color="transparent"
              :color="$theme.whitehigh"
              hide-slider right
              >
              <v-tab 
                v-for="(page, index) in links" 
                :key="index" 
                :to="`/product/${product_key}/${page}`"
                class="display" >
                <span >{{ page }}</span>
              </v-tab>
            </v-tabs>
          </v-col>  
        </v-row>  

        <v-card outlined elevation="4" class="flex-grow-1">
            <router-view></router-view>
        </v-card>

      </v-container>
    </v-card>
  </v-dialog>
</template>

<script>
export default {

  name: 'ModalScreen',
  props: ['product_key', 'title'],

  data() {
    return {
      previousPage: '',
      activePageIndex: 0,
      links: ['home', 'process', 'bom']
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
