<template>
  <v-container fluid class="ma-0 py-2">
    <v-row cols=12>
      <v-app-bar-nav-icon style="color: rgba(255,255,255,.6);"></v-app-bar-nav-icon>
      <h3 class="d-flex align-center display">Library</h3>
      <!-- <v-avatar class="d-flex align-center display ml-auto mr-3"> -->
      <h5 class="d-flex align-center display highlight ml-auto">Josh White</h5>
      <v-avatar size="28" class="d-flex my-auto mr-3 ml-2">
        <img src="pics/users/Josh White.jpg">
      </v-avatar>
    </v-row>
  </v-container>
</template>

<script>
export default {

  name: 'AppBar',

  data () {
    return {

    }
  }
}
</script>

<style lang="css" scoped>
</style>