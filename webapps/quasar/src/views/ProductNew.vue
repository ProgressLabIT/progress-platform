<template>
  <BaseModalForm
    id="new-product-form"
    @submit="postNewProduct"
    max_width="700px"
    @cancel="$router.back()">

    <template #title>
      {{ $t('product.new_modal_title') }}
    </template>

    <template #form>
      <q-input
        :label="$capitalize($t('code'))"
        v-model="new_product_code"
        class="input-uppercase"
        clearable>
      </q-input>
      <q-input
        type="textarea"
        clearable
        :label="$capitalize($t('description'))"
        v-model="new_product_desc">
      </q-input>
      <q-file
        :label="$t('image')"
        accept="image/*"
        clearable
        counter>
        <template #append>
          <q-icon name="mdi-image" />
        </template>
      </q-file>
    </template>

  </BaseModalForm>
</template>

<script>
import { api } from '@/boot/axios.js'

import BaseModalForm from '@/components/BaseDialog.vue'

export default {

  name: 'NewProduct',

  components: {
    BaseModalForm
  },

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
            params: { product_key: new_product_data._key },
            query: { back_to: 'productList' }
          })
        })
        .catch(error => {
          window.alert("Couldn't save product, try again.", error)
          this.$router.back()
        })
    }
  },

  created() {
    console.log('Creato')
  }
};
</script>

<style lang="css" scoped>
</style>
