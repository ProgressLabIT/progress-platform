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
            class="input-uppercase"
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
import { api } from '@/lib/apiCall.js'

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

    postNewProduct() {
      let body = new FormData()
      const code = this.new_product_code.toUpperCase()
      const desc = this.new_product_desc


      body.append("code", code)
      body.append("description", desc)

      if (this.new_product_pic) {
        const image = this.new_product_pic
        body.append("image", image, image.name)
      }
      
      api.post('product', body, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })
        .then(resp => {
          // Go back to product list
          const new_product_data = resp.data.detail
          this.$store.commit('ADD_NEW_PRODUCT', new_product_data)
          this.$store.commit('LOAD_PRODUCT_DETAILS', new_product_data)
          this.$router.push({ 
            name: 'productHome', 
            params: { item_key: new_product_data._key },
            query: { back_to: 'productList' }
          })
        })
        .catch(error => {
          window.alert("Couldn't save product, try again.", error)
          this.$router.back()
        })
        

    }
  }
};
</script>

<style lang="css" scoped>
</style>
