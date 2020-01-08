<template>
  <v-dialog 
    value="true" 
    :overlay-color="$theme.background"
    overlay-opacity="1"
    max-width="500px"
    persistent no-click-animation>
    <v-card>
      <v-card-title>
        <h3 class="display">nuovo prodotto</h3>
      </v-card-title>
      <v-card-text>
        <v-form>  
          <v-text-field
            clearable
            counter="20"
            label="Codice"
            v-model="new_product_code"
            />
          <v-textarea
            clearable
            auto-grow
            counter="500"
            label="Descrizione"
            v-model="new_product_desc"
            />
          <v-file-input 
            clearable
            label="Immagine" 
            accept="image/*"
            prepend-icon=""
            append-icon="image"
            v-model="new_product_pic"
            />
        <v-row class="mt-6">
          <v-col>
            <v-btn block depressed color="primary">salva</v-btn>
          </v-col>
          <v-col>    
            <v-btn block depressed :color="$theme.grey" @click="$router.back()">annulla</v-btn>
          </v-col>    
        </v-row>  
        </v-form>
      </v-card-text>
    </v-card>
  </v-dialog>
</template>

<script>
export default {

  name: 'NewProduct',

  data() {
    return {
      new_product_code: '',
      new_product_desc: '',
      new_product_pic: []  
    };
  }
};
</script>

<style lang="css" scoped>
</style>
