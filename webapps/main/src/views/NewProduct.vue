<template>
  <v-dialog 
    value="true" 
    :overlay-color="$vuetify.theme.themes.dark.colors.background"
    overlay-opacity="1"
    persistent no-click-animation>
    <v-card outlined>
      <v-card-title>
        <h3 class="display">NEW PRODUCT</h3>
      </v-card-title>
            This is a test
          <v-btn size="x-large" color="error">BIG BUTTON</v-btn>
    </v-card>
  </v-dialog>
</template>

<script>
export default {

  name: 'NewProduct',

  data() {
    return {

    };
  },
};
</script>

<style lang="css" scoped>
</style>
