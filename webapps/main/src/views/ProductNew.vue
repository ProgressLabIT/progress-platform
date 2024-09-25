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

        <q-toggle
          v-model="new_product_traceability_enabled"
          :label="$t('traceability.enabled')"
        />

        <q-input
          v-if="new_product_traceability_enabled"
          v-model="new_product_counter_name"
          dense
          :label="$capitalize($t('counter'))"
          class="input-uppercase"
          clearable
          @click="show_new_counter_form = true"
        >
        </q-input>
      </div>
      <BaseDialog :show="show_new_counter_form" :no-backdrop-dismiss="false">
        <CounterSearch
          @close="show_new_counter_form = false"
          @select="selectCounter"
        >
        </CounterSearch>
      </BaseDialog>
    </template>
  </BaseModalForm>
</template>

<script>
import { api } from '@/boot/axios.js';

import BaseDialog from '@/components/BaseDialog.vue';
import BaseModalForm from '@/components/BaseModalForm.vue';
import CounterSearch from '../components/settings/counters/CounterSearch.vue';

export default {
  name: 'ProductNew',

  components: {
    BaseModalForm,
    CounterSearch,
    BaseDialog,
  },

  data() {
    return {
      new_product_code: '',
      new_product_desc: '',
      new_product_pic: null,
      new_product_traceability_enabled: false,
      new_product_counter: null,
      new_product_counter_name: '',
      show_new_counter_form: false,
    };
  },

  methods: {
    selectCounter(counter) {
      this.new_product_counter = counter;
      this.new_product_counter_name = counter.name;
      this.show_new_counter_form = false;
    },

    postNewProduct() {
      let body = new FormData();

      body.append('code', this.new_product_code.toUpperCase());
      body.append('description', this.new_product_desc);
      body.append(
        'traceability_level',
        this.new_product_traceability_enabled ? 'form_only' : '',
      );

      if (this.new_product_pic) {
        const image = this.new_product_pic;
        body.append('image', image, image.name);
      }

      if (this.new_product_counter) {
        body.append('counter_key', this.new_product_counter._key);
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
