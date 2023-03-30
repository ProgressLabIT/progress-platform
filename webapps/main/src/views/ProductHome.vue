<template>
  <div class="row full-height q-pa-md">
    <!-- LEFT COLUMN -->
    <div class="col-4 column full-height q-pr-md">
      <!-- PRODUCT IMAGE -->
      <div class="relative-position col-auto"
        style="border: solid 1px rgba(255,255,255,.12); height: 30vh;">
        <q-img
          class="fit"
          :src="img_src"
          @mouseenter="over_image = true"
          @mouseleave="over_image = false"
          :style="product.active ? '' : 'filter:grayscale(1) brightness(.5)'">
        </q-img>
        <div class="absolute-full column q-pa-md">
          <q-btn
            v-if="over_image && !edit_mode && !no_image"
            class="absolute-bottom-right q-ma-md"
            color="theme-grey"
            size="12px"
            @click.stop="showMedia('img')">
            <q-icon name="mdi-magnify" />
          </q-btn>

          <template v-if="edit_mode">
            <div class="absolute-top text-center q-py-xs" style="background: rgba(0, 0, 0, .5);">
              {{ $capitalize($t('product.update_image')) }}
            </div>

            <q-space />

            <div class="row">
              <q-btn
                v-if="new_image || new_image_url === 'deleted'"
                size="12px"
                color="theme-orange"
                @click="clearTempImg">
                {{ $t('product.restore_image') }}
              </q-btn>
              <q-btn
                v-else-if="!no_image"
                size="12px"
                color="theme-red"
                @click="deleteImg">
                <q-icon name="mdi-delete" />
              </q-btn>
              <q-space />
              <input
                type="file"
                ref="upload_img"
                style="display: none"
                accept="image/*"
                @change="updateImg($event.target.files[0])" />
              <q-btn
                size="12px"
                color="theme-grey"
                @click="$refs.upload_img.click()">
                <q-icon name="mdi-upload" />
              </q-btn>
              <q-btn
                v-if="img_src != ''"
                size="12px"
                color="theme-grey"
                @click.stop="showMedia('img')"
                class="q-ml-sm">
                <q-icon name="mdi-magnify" />
              </q-btn>
            </div>
          </template>
        </div>

        <div v-if="no_image" class="column absolute-full flex-center">
          <q-icon
            size="xl"
            color="text-low"
            name="mdi-image-off-outline">
          </q-icon>
          <div>
            {{ $t('product.no_image') }}
          </div>
        </div>
      </div>

      <!-- PRODUCT CODE -->
      <div class="q-mt-lg col-auto">
        <div class="text-h4 weight-bold text-uppercase">
          {{ $t('product.code') }}
        </div>
        <div v-if="!edit_mode" class="text-h1 display highlight">
          {{ product.code }}
        </div>
        <q-input v-else filled dense
          :model-value="temp_code"
          @update:model-value="value => updateField('code', value.toUpperCase())"
          class="input-uppercase q-mt-md">
        </q-input>
      </div>

      <!-- PRODUCT DESCRIPTION -->
      <div class="q-mt-lg col-auto">
        <div class="text-h4 weight-bold text-uppercase">
          {{ $t('description') }}
        </div>
        <div v-if="!edit_mode" class="text-h3 highlight weight-bold q-mt-xs">
          {{ product.description }}
        </div>
        <q-input v-else
          filled dense type="textarea"
          :model-value="temp_desc"
          @update:model-value="value => updateField('description', value)"
          class="q-mt-md">
        </q-input>
      </div>

      <q-space />

      <!-- EDIT MODE ACTIONS -->
      <div class="col-auto">
        <q-btn
          v-if="!edit_mode"
          color="theme-blue"
          class="full-width"
          @click="activateEditMode">
          {{ $t('edit') }}
        </q-btn>

        <div v-else>
          <q-btn
            class="full-width q-mb-sm"
            :loading="saving"
            color="theme-green"
            @click="saveChanges">
            {{ $t('save') }}
          </q-btn>
          <q-btn
            class="full-width"
            color="theme-grey"
            :disabled="saving"
            @click="cancelChanges">
            {{ $t('cancel') }}
          </q-btn>
        </div>
      </div>
    </div>
    <!-- END OF LEFT COLUMN -->

    <!-- RIGHT SECTION -->

    <!-- NOTES -->
    <div class="col-4 q-px-md">
      <q-card square class="surface2 q-px-sm q-pt-sm q-pb-md">
        <q-card-section class="text-h5 display weight-bold text-uppercase">
          {{ $t('notes_production') }}
        </q-card-section>
        <q-card-section>
          <div v-if="!edit_mode" style="white-space: pre-line;">
            {{ temp_notes }}
          </div>
          <q-input
            v-else
            filled
            dense
            type="textarea"
            :readonly="!edit_mode"
            :model-value="temp_notes"
            @update:model-value="value => updateField('production_notes', value)"
            class="q-mt-md">
          </q-input>
        </q-card-section>
      </q-card>
    </div>

    <!-- DOCS -->
    <div class="col-4 q-pl-md">
      <q-card square class="surface2 q-px-sm q-pt-sm q-pb-md">
        <q-card-section class="text-h5 display highlight">
          {{ $capitalize($t('document.label', 2)) }}
        </q-card-section>
        <q-list>
          <q-item
            v-for="(doc, index) in docs"
            :key="index"
            clickable
            @click="showMedia(index)">
            <q-item-section
              class="col"
              :class="{ 'text-italic': doc.temp}">
              {{ doc.name }} {{ doc.temp ? '(' + $capitalize($t('unsaved')) + ')' : '' }}
            </q-item-section>
            <q-item-section class="col-1">
              <q-icon
                v-if="edit_mode"
                name="mdi-close"
                class="hover-red"
                @click.stop="deleteDoc(index)">
              </q-icon>
            </q-item-section>
            <q-item-section class="col-auto text-right">
              {{ $bytes(doc.size) }}
            </q-item-section>
          </q-item>
        </q-list>

        <input
          multiple
          type="file"
          ref="upload_doc"
          style="display: none"
          accept="application/pdf, image/*"
          @change="addFiles($event.target.files)"/>
        <q-btn
          v-if="edit_mode"
          flat
          class="full-width"
          color="theme-blue"
          @click="$refs.upload_doc.click()">
          <span>{{ $t('document.add', 2) }}</span>
          <q-space />
          <q-icon name="mdi-paperclip" />
        </q-btn>

      </q-card>

      <!-- DOCUMENT VIEWER -->
      <MediaViewer
        v-if="show_media >= 0 || show_media === 'img' "
        :show="show_media >= 0 || show_media === 'img' "
        @close="show_media = -1"
        v-bind="{ media_name, media_src }">
        <template #context-title>
          {{ $t('product.code').toUpperCase() }}: {{ product.code }}
        </template>
      </MediaViewer>

    </div>
  </div>
</template>

<script>
import ProductParamsCard from '@/components/ProductParamsCard.vue'
import { mapState, mapActions } from 'vuex'
import MediaViewer from '@/components/MediaViewer.vue'
// import BaseConfirmationDialog from '@/components/BaseConfirmationDialog.vue'

export default {

  name: 'ProductHome',
  
  components: {
    // BaseConfirmationDialog,
    MediaViewer,
    ProductParamsCard
  },

  data() {
    return {
      over_image: false,
      saving: false,
      show_delete_confirmation: false,
      show_cancel_confirmation: false,
      show_save_confirmation: false,
      show_media: -1,
      new_files: null,
      new_image: null,
      new_image_url: '',
      no_image: false
      // zoom: 100
    };
  },

  computed: {

    product_key() {
      return this.$route.params.product_key
    },

    ...mapState({
      product: state => state.product.temp
    }),

    edit_mode: {
      get() {
        return this.$store.state.product.edit_modes.product
      },
      set(value) {
        this.$store.commit('TOGGLE_EDIT_MODE', { view: 'product', value })
      }
    },

    saved_img_path() {
      return `/media/product/${this.product_key}/image.jpg`
    },

    img_src() {
      return this.new_image_url ? this.new_image_url : this.saved_img_path
    },

    temp_code() {
      return this.product.code
    },

    temp_desc() {
      return this.product.description
    },

    temp_notes() {
      return this.product.production_notes
    },

    docs() {
      return this.product.docs
    },

    saved_docs() {
      return this.$store.state.product.saved.docs
    },

    media_name() {
      if (this.show_media == -1) { return '' }
      else if (this.show_media === 'img') { return 'Product image'}
      else { return this.docs[this.show_media].name }
    },

    media_src() {
      
      if (this.show_media === 'img') {
        return this.img_src
      }

      else if (this.show_media >= 0) {
        const doc = this.docs[this.show_media]
        let path = ''

        if (doc.temp) {
          path = window.URL.createObjectURL(doc.data)
        }
        else path = `/media/product/${this.product_key}/doc/${encodeURI(this.media_name)}`

        return path
      }

      else return null
    },

  },

  methods: {
    ...mapActions(['loadProductDetails']),

    // deltaPcString(p) {
    //   let pc_sign = p.delta_pc > 0 ? '+' : ''
    //   return '('.concat(pc_sign, p.delta_pc, '%)')
    // },

    activateEditMode() {
      this.temp_code = this.product.code
      this.temp_desc = this.product.description

      this.edit_mode = true
    },

    updateImg(img) {
      // let url = this.new_image_url
      // if (url) window.URL.revokeObjectURL(url)
      this.new_image_url = window.URL.createObjectURL(img)
      this.new_image = img
      this.no_image = false
    },

    clearTempImg() {
      window.URL.revokeObjectURL(this.new_image_url)
      this.new_image_url = null
      this.new_image = null
      this.no_image = false
    },

    deleteImg() {
      // this is a fake URL to make v-img show placeholder
      this.new_image_url = 'deleted'
    },

    updateField(field, value) {
      this.$store.commit('UPDATE_TEMP_PARAMETER', { 
        param: field, 
        new_value: value 
      })
    },

    addFiles(file_list) {
      const files = Array.from(file_list)
      // Don't add files already in the list
      files.forEach( (f, i) => {
        const already_in_list = this.docs.some( d => f.name == d.name )
        if (already_in_list) {
          const replace = window.confirm(
            this.$capitalize(this.$t('product.alerts.doc_name_exists',1, {filename: f.name}))
          )
          if (replace) { this.$store.commit('DELETE_TEMP_DOC', i) }
          else { return }
        }
        this.$store.commit('ADD_TEMP_DOC', f)
      }) 
    },

    deleteDoc(index) {
      this.$store.commit('DELETE_TEMP_DOC', index)
    },

    showMedia(value) {
        this.show_media = value
    },

    saveChanges() {
      this.saving = true
      const old_doc_list = this.$store.state.product.saved.docs
      const new_doc_list = this.product.docs
      let product_update = {
        new_product_data: this.product,
        deleted_docs: old_doc_list.filter( 
          o => !new_doc_list.some( n => n.name === o.name)
        ),
        image: {
          new: this.new_image,
          delete: this.new_image_url === 'deleted'
        }
      }

      if (new_doc_list){
        product_update.new_docs = new_doc_list.filter( d => 'temp' in d )
      }

      this.$store.dispatch('saveProductChanges', product_update)
        .then(async () => {
        // Show progress long enough the let user notice something is going on
        // even if the update is instantaneous
          // setTimeout(() => {
            await this.$store.dispatch('loadProductDetails', this.product_key)
            this.$emit('changes_saved')
            this.edit_mode = false
            this.clearTempImg()
            this.saving = false
          // }, 1500)
        })
        .catch(err => {
          window.alert(err)
        })
    },

    cancelChanges() {
      this.$store.commit('CANCEL_PRODUCT_CHANGES')
      this.$emit('changes_canceled')
      this.edit_mode = false
    },

    // deleteProduct() {
    //   this.$store.dispatch('moveToTrash', this.product)
    //   this.$router.push({ name: 'productList' })
    // }
  },

  watch: {
    img_src() {
      if (!this.img_src.startsWith('blob')) {
        let test = new XMLHttpRequest()
        test.open('HEAD', this.img_src, false)
        test.send()
        if (test.status === 404) {
          this.no_image = true
        }
      }
    }
  }
};
</script>

<style lang="css" scoped>
</style>
