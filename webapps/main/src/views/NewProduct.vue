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
            show-size
            v-model="new_product_pic"
            />
        <v-row class="mt-6">
          <v-col>
            <v-btn block depressed color="primary" @click="postNewProduct">salva</v-btn>
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
import axios from 'axios'
import { mapActions } from 'vuex'

export default {

  name: 'NewProduct',

  data() {
    return {
      new_product_code: '',
      new_product_desc: '',
      new_product_pic: null  
    };
  },

  methods: {

    ...mapActions(['addNewProduct']),

    postNewProduct() {
      // console.log("Preparing form data...")
      let body = new FormData()
      body.set("code", this.new_product_code)
      body.set("description", this.new_product_desc)

      if (this.new_product_pic) {
        // console.log("found image! Adding to body...")
        const image = this.new_product_pic
        body.append("image", image, image.name)
      }
      
      // console.log("Posting form data...")
      axios({
          method: 'post', 
          url: 'http://127.0.0.1:8000/product',
          data: body,
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })
        .then(resp => {
          console.log(resp)
          // Go back to product list
          const newProductData = resp.data.data
          this.addNewProduct(newProductData)
          this.$router.push({ name: 'productList'})
        })
        .catch(error => console.log(error.response))
    }
  }
};
</script>

<style lang="css" scoped>
</style>
