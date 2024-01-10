<template>
  <BaseModalForm
    id="new-product-form"
    :show="true"
    max-width="700px"
    maximized
    @submit="postNewProduct"
    @cancel="$router.back()"
  >
    <template #title>
      {{ $t('product.new_modal_title') }}
    </template>

    <template #form>
      <div class="column q-gutter-lg" style="min-width: 400px">
        <q-input
          v-model="new_product_code"
          dense
          :label="$capitalize($t('code'))"
          class="input-uppercase"
          clearable
        >
        </q-input>
        <q-input
          v-model="new_product_desc"
          dense
          type="textarea"
          clearable
          :label="$capitalize($t('description'))"
        >
        </q-input>
        <q-file
          v-model="new_product_pic"
          dense
          :label="$capitalize($t('image'))"
          accept="image/*"
          clearable
          counter
        >
          <template #append>
            <q-icon name="mdi-image" />
          </template>
        </q-file>
      </div>
    </template>
  </BaseModalForm>
</template>

<script>
import { api } from '@/boot/axios.js';

import BaseModalForm from '@/components/BaseModalForm.vue';

export default {
  name: 'ProductNew',

  components: {
    BaseModalForm,
  },

  data() {
    return {
      new_product_code: '',
      new_product_desc: '',
      new_product_pic: null,
    };
  },

  methods: {
    postNewProduct() {
      let body = new FormData();
      const code = this.new_product_code.toUpperCase();
      const desc = this.new_product_desc;

      body.append('code', code);
      body.append('description', desc);

      if (this.new_product_pic) {
        const image = this.new_product_pic;
        body.append('image', image, image.name);
      }

      api
        .post('product', body, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        })
        .then((resp) => {
          // Go back to product list
          const new_product_data = resp.data.detail;
          this.$store.commit('ADD_NEW_PRODUCT', new_product_data);
          this.$store.commit('LOAD_PRODUCT_DETAILS', new_product_data);
          this.$router.push({
            name: 'productHome',
            params: { product_key: new_product_data._key },
            query: { back_to: 'productList' },
          });
        })
        .catch((error) => {
          window.alert("Couldn't save product, try again.", error);
        });
    },
  },
};
</script>
